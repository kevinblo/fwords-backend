import logging
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, EmailActivationToken, LanguageProgress, WordsProgress, QuizProgress
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    ResendActivationSerializer,
    LanguageProgressSerializer,
    WordsProgressSerializer,
    QuizProgressSerializer,
)

# Configure logger for profile access
profile_logger = logging.getLogger('users.profile')

# Configure logger for progress endpoints
progress_logger = logging.getLogger('users.progress')

# Configure console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
console_handler.setFormatter(formatter)

# Add console handler to profile logger if not already present
if not any(isinstance(handler, logging.StreamHandler) for handler in profile_logger.handlers):
    profile_logger.addHandler(console_handler)
    profile_logger.setLevel(logging.INFO)

# Add console handler to progress logger if not already present
if not any(isinstance(handler, logging.StreamHandler) for handler in progress_logger.handlers):
    progress_logger.addHandler(console_handler)
    progress_logger.setLevel(logging.INFO)


class UserRegistrationView(generics.CreateAPIView):
    """User registration endpoint"""
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Register a new user",
        responses={
            201: openapi.Response('User registered successfully'),
            400: 'Bad Request'
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Create activation token
            activation_token = EmailActivationToken.objects.create(user=user)

            # Send activation email
            self.send_activation_email(user, activation_token, request)

            return Response({
                'message': 'User registered successfully. Please check your email to activate your account.',
                'user_id': user.id
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def send_activation_email(self, user, token, request):
        """Send activation email to user"""
        current_site = get_current_site(request)
        activation_url = f"http://{current_site.domain}/api/auth/activate/{token.token}/"

        subject = 'Activate your ForeignWords account'
        message = f"""
        Hi {user.name or user.email},
        
        Thank you for registering with ForeignWords!
        
        Please click the link below to activate your account:
        {activation_url}
        
        This link will expire in 24 hours.
        
        If you didn't create this account, please ignore this email.
        
        Best regards,
        ForeignWords Team
        """

        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Failed to send activation email: {e}")


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
@swagger_auto_schema(
    operation_description="Activate user email",
    responses={
        200: 'Email activated successfully',
        400: 'Invalid or expired token'
    }
)
def activate_email(request, token):
    """Activate user email with token"""
    try:
        activation_token = EmailActivationToken.objects.get(token=token, is_used=False)

        if activation_token.is_expired():
            return Response({
                'error': 'Activation token has expired'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Activate user
        user = activation_token.user
        user.is_active = True
        user.is_email_verified = True
        user.save()

        # Mark token as used
        activation_token.is_used = True
        activation_token.save()

        return Response({
            'message': 'Email activated successfully. You can now login.'
        }, status=status.HTTP_200_OK)

    except EmailActivationToken.DoesNotExist:
        return Response({
            'error': 'Invalid or expired activation token'
        }, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(generics.GenericAPIView):
    """User login endpoint"""
    serializer_class = UserLoginSerializer
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Login user and get JWT tokens",
        responses={
            200: openapi.Response('Login successful'),
            400: 'Bad Request'
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)

            return Response({
                'message': 'Login successful',
                'user': UserProfileSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """User profile endpoint"""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    # Sensitive fields that should not be logged in full
    SENSITIVE_FIELDS = {'password', 'old_password', 'new_password', 'password1', 'password2'}

    def get_object(self):
        return self.request.user

    def log_profile_access(self, request, action, response_status=None):
        """Log profile access with detailed information"""
        user = request.user
        client_ip = self.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')

        log_message = (
            f"Profile {action} - User: {user.email} (ID: {user.id}), "
            f"IP: {client_ip}, Status: {response_status or 'N/A'}, "
            f"User-Agent: {user_agent[:100]}..."
        )

        # Log to configured logger
        profile_logger.info(log_message)

        # Also print to console for immediate visibility
        print(f"[PROFILE ACCESS] {log_message}")

    def get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'Unknown')
        return ip

    def sanitize_field_value(self, field_name, value):
        """Sanitize sensitive field values for logging"""
        if field_name.lower() in self.SENSITIVE_FIELDS:
            return "***HIDDEN***"

        # Truncate very long values
        if isinstance(value, str) and len(value) > 100:
            return f"{value[:97]}..."

        return value

    def format_update_data(self, data):
        """Format update data for logging with field names and values"""
        if not data:
            return "No data"

        formatted_fields = []
        for field_name, value in data.items():
            sanitized_value = self.sanitize_field_value(field_name, value)
            formatted_fields.append(f"{field_name}: '{sanitized_value}'")

        return "{" + ", ".join(formatted_fields) + "}"

    @swagger_auto_schema(
        operation_description="Get user profile",
        responses={200: UserProfileSerializer}
    )
    def get(self, request, *args, **kwargs):
        # Log profile access attempt
        self.log_profile_access(request, 'GET_ATTEMPT')

        try:
            response = super().get(request, *args, **kwargs)
            # Log successful profile retrieval
            self.log_profile_access(request, 'GET_SUCCESS', response.status_code)
            return response
        except Exception as e:
            # Log failed profile retrieval
            error_message = (
                f"Profile GET failed - User: {request.user.email} (ID: {request.user.id}), "
                f"IP: {self.get_client_ip(request)}, Error: {str(e)}"
            )
            profile_logger.error(error_message)
            print(f"[PROFILE ERROR] {error_message}")
            self.log_profile_access(request, 'GET_ERROR', 500)
            raise

    @swagger_auto_schema(
        operation_description="Update user profile",
        responses={200: UserProfileSerializer}
    )
    def patch(self, request, *args, **kwargs):
        # Log profile update attempt
        self.log_profile_access(request, 'UPDATE_ATTEMPT')

        # Log the fields being updated with their values
        update_data = request.data if hasattr(request, 'data') else {}
        formatted_data = self.format_update_data(update_data)

        fields_message = (
            f"Profile UPDATE data - User: {request.user.email} (ID: {request.user.id}), "
            f"IP: {self.get_client_ip(request)}, Data: {formatted_data}"
        )
        profile_logger.info(fields_message)
        print(f"[PROFILE UPDATE] {fields_message}")

        # Also log just field names for quick overview
        field_names = list(update_data.keys()) if update_data else []
        overview_message = (
            f"Profile UPDATE fields overview - User: {request.user.email} (ID: {request.user.id}), "
            f"Fields: {field_names}, Count: {len(field_names)}"
        )
        profile_logger.info(overview_message)
        print(f"[PROFILE UPDATE OVERVIEW] {overview_message}")

        # Log current user state before update
        user = self.get_object()
        current_native_language = getattr(user, 'native_language', 'NOT_SET')
        print(f"[PROFILE DEBUG] Current native_language before update: '{current_native_language}'")

        try:
            # Get serializer and validate
            print(f"[PROFILE DEBUG] Getting serializer with data: {update_data}")
            serializer = self.get_serializer(user, data=update_data, partial=True)

            print(f"[PROFILE DEBUG] Validating serializer...")
            if serializer.is_valid():
                print(f"[PROFILE DEBUG] Serializer is valid. Validated data: {serializer.validated_data}")

                # Save the instance
                print(f"[PROFILE DEBUG] Saving serializer...")
                updated_user = serializer.save()

                # Check if the field was actually updated
                new_native_language = getattr(updated_user, 'native_language', 'NOT_SET')
                print(f"[PROFILE DEBUG] native_language after save: '{new_native_language}'")

                # Refresh from database to double-check
                updated_user.refresh_from_db()
                db_native_language = getattr(updated_user, 'native_language', 'NOT_SET')
                print(f"[PROFILE DEBUG] native_language from DB after refresh: '{db_native_language}'")

                # Create response
                response_data = serializer.data
                response = Response(response_data, status=status.HTTP_200_OK)

                # Log successful profile update
                self.log_profile_access(request, 'UPDATE_SUCCESS', response.status_code)

                # Log successful update summary
                success_message = (
                    f"Profile UPDATE completed successfully - User: {request.user.email} (ID: {request.user.id}), "
                    f"Updated fields: {len(field_names)}, IP: {self.get_client_ip(request)}"
                )
                profile_logger.info(success_message)
                print(f"[PROFILE UPDATE SUCCESS] {success_message}")

                return response
            else:
                # Log serializer validation errors
                validation_errors = serializer.errors
                error_message = (
                    f"Profile UPDATE validation failed - User: {request.user.email} (ID: {request.user.id}), "
                    f"IP: {self.get_client_ip(request)}, Errors: {validation_errors}, "
                    f"Attempted data: {formatted_data}"
                )
                profile_logger.error(error_message)
                print(f"[PROFILE VALIDATION ERROR] {error_message}")

                return Response(validation_errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            # Log failed profile update
            error_message = (
                f"Profile UPDATE failed - User: {request.user.email} (ID: {request.user.id}), "
                f"IP: {self.get_client_ip(request)}, Error: {str(e)}, "
                f"Attempted data: {formatted_data}"
            )
            profile_logger.error(error_message)
            print(f"[PROFILE ERROR] {error_message}")
            self.log_profile_access(request, 'UPDATE_ERROR', 500)
            raise


class ResendActivationView(generics.GenericAPIView):
    """Resend activation email endpoint"""
    serializer_class = ResendActivationSerializer
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Resend activation email",
        responses={
            200: 'Activation email sent',
            400: 'Bad Request'
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = User.objects.get(email=email)

            # Create new activation token
            activation_token = EmailActivationToken.objects.create(user=user)

            # Send activation email
            UserRegistrationView().send_activation_email(user, activation_token, request)

            return Response({
                'message': 'Activation email sent successfully'
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@swagger_auto_schema(
    operation_description="Logout user (blacklist refresh token)",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'refresh_token': openapi.Schema(type=openapi.TYPE_STRING)
        }
    ),
    responses={
        200: 'Logout successful',
        400: 'Bad Request'
    }
)
def logout_view(request):
    """Logout user by blacklisting refresh token"""
    try:
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()

        return Response({
            'message': 'Logout successful'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': 'Invalid token'
        }, status=status.HTTP_400_BAD_REQUEST)


class ProgressLoggingMixin:
    """Mixin to add detailed logging to progress endpoints"""

    def get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'Unknown')
        return ip

    def get_user_agent(self, request):
        """Get user agent from request"""
        return request.META.get('HTTP_USER_AGENT', 'Unknown')[:200]

    def format_query_params(self, request):
        """Format query parameters for logging"""
        # Handle both Django request and DRF request objects
        query_params = getattr(request, 'query_params', None) or request.GET

        if not query_params:
            return "None"

        params = []
        for key, value in query_params.items():
            # Truncate very long values
            if isinstance(value, str) and len(value) > 100:
                value = f"{value[:97]}..."
            params.append(f"{key}={value}")

        return "{" + ", ".join(params) + "}"

    def format_request_data(self, request):
        """Format request data for logging"""
        if not hasattr(request, 'data') or not request.data:
            return "None"

        # For bulk operations, show summary instead of full data
        if isinstance(request.data, dict) and 'updates' in request.data:
            updates = request.data.get('updates', [])
            return f"{{bulk_updates: {len(updates)} items}}"

        # For regular data, show field names and truncated values
        formatted_fields = []
        for field_name, value in request.data.items():
            if isinstance(value, str) and len(value) > 50:
                value = f"{value[:47]}..."
            formatted_fields.append(f"{field_name}: '{value}'")

        return "{" + ", ".join(formatted_fields) + "}"

    def log_progress_request(self, request, action, endpoint, additional_info="", response_status=None, error=None):
        """Log progress request with detailed information"""
        user = getattr(request, 'user', None)
        user_info = f"{user.email} (ID: {user.id})" if user and user.is_authenticated else "Anonymous"

        client_ip = self.get_client_ip(request)
        user_agent = self.get_user_agent(request)
        query_params = self.format_query_params(request)
        request_data = self.format_request_data(request)

        # Build log message
        log_parts = [
            f"PROGRESS {action}",
            f"Endpoint: {endpoint}",
            f"User: {user_info}",
            f"IP: {client_ip}",
            f"Status: {response_status or 'N/A'}",
            f"Query: {query_params}",
            f"Data: {request_data}",
            f"User-Agent: {user_agent}"
        ]

        if additional_info:
            log_parts.append(f"Info: {additional_info}")

        if error:
            log_parts.append(f"Error: {str(error)}")

        log_message = " | ".join(log_parts)

        # Log to configured logger
        if error:
            progress_logger.error(log_message)
        else:
            progress_logger.info(log_message)

        # Also print to console for immediate visibility
        log_prefix = "[PROGRESS ERROR]" if error else "[PROGRESS]"
        print(f"{log_prefix} {log_message}")

    def log_queryset_info(self, request, queryset, endpoint):
        """Log information about the queryset being returned"""
        try:
            count = queryset.count() if hasattr(queryset, 'count') else len(queryset)
            user = getattr(request, 'user', None)
            user_info = f"{user.email} (ID: {user.id})" if user and user.is_authenticated else "Anonymous"

            info_message = f"Queryset info - User: {user_info}, Endpoint: {endpoint}, Results: {count} items"
            progress_logger.info(info_message)
            print(f"[PROGRESS QUERYSET] {info_message}")
        except Exception as e:
            error_message = f"Failed to log queryset info for {endpoint}: {str(e)}"
            progress_logger.error(error_message)
            print(f"[PROGRESS ERROR] {error_message}")

    def dispatch(self, request, *args, **kwargs):
        """Override dispatch to log all requests"""
        endpoint = f"{request.path}"
        method = request.method

        # Log request attempt
        self.log_progress_request(request, f"{method}_ATTEMPT", endpoint)

        try:
            # Call the parent dispatch method
            response = super().dispatch(request, *args, **kwargs)

            # Log successful response
            self.log_progress_request(
                request,
                f"{method}_SUCCESS",
                endpoint,
                response_status=response.status_code
            )

            return response

        except Exception as e:
            # Log error
            self.log_progress_request(
                request,
                f"{method}_ERROR",
                endpoint,
                error=e,
                response_status=500
            )
            raise


class LanguageProgressListCreateView(ProgressLoggingMixin, generics.ListCreateAPIView):
    """List and create language progress for authenticated user"""
    serializer_class = LanguageProgressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Handle Swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return LanguageProgress.objects.none()

        queryset = LanguageProgress.objects.filter(user=self.request.user)

        # Log queryset info
        if hasattr(self, 'request'):
            self.log_queryset_info(self.request, queryset, 'language-progress-list')

        return queryset

    @swagger_auto_schema(
        operation_description="Get user's language learning progress",
        responses={200: LanguageProgressSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)

        # Log additional info about the response
        result_count = len(response.data) if hasattr(response, 'data') and response.data else 0
        self.log_progress_request(
            request,
            'GET_RESULT',
            request.path,
            additional_info=f"Returned {result_count} language progress entries"
        )

        return response

    @swagger_auto_schema(
        operation_description="Create new language progress entry",
        responses={
            201: LanguageProgressSerializer,
            400: 'Bad Request'
        }
    )
    def post(self, request, *args, **kwargs):
        # Log creation attempt details
        language_id = request.data.get('language') if hasattr(request, 'data') else None
        self.log_progress_request(
            request,
            'CREATE_ATTEMPT',
            request.path,
            additional_info=f"Creating progress for language_id: {language_id}"
        )

        response = super().post(request, *args, **kwargs)

        # Log creation result
        if response.status_code == 201:
            created_id = response.data.get('id') if hasattr(response, 'data') else None
            self.log_progress_request(
                request,
                'CREATE_SUCCESS',
                request.path,
                additional_info=f"Created language progress with ID: {created_id}"
            )

        return response


class LanguageProgressDetailView(ProgressLoggingMixin, generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete specific language progress"""
    serializer_class = LanguageProgressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Handle Swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return LanguageProgress.objects.none()
        return LanguageProgress.objects.filter(user=self.request.user)

    @swagger_auto_schema(
        operation_description="Get specific language progress",
        responses={200: LanguageProgressSerializer}
    )
    def get(self, request, *args, **kwargs):
        progress_id = kwargs.get('pk')
        self.log_progress_request(
            request,
            'GET_DETAIL_ATTEMPT',
            request.path,
            additional_info=f"Retrieving language progress ID: {progress_id}"
        )

        response = super().get(request, *args, **kwargs)

        if response.status_code == 200:
            language_name = response.data.get('language_name') if hasattr(response, 'data') else 'Unknown'
            self.log_progress_request(
                request,
                'GET_DETAIL_SUCCESS',
                request.path,
                additional_info=f"Retrieved progress for language: {language_name}"
            )

        return response

    @swagger_auto_schema(
        operation_description="Update language progress",
        responses={200: LanguageProgressSerializer}
    )
    def patch(self, request, *args, **kwargs):
        progress_id = kwargs.get('pk')
        self.log_progress_request(
            request,
            'UPDATE_DETAIL_ATTEMPT',
            request.path,
            additional_info=f"Updating language progress ID: {progress_id}"
        )

        response = super().patch(request, *args, **kwargs)

        if response.status_code == 200:
            self.log_progress_request(
                request,
                'UPDATE_DETAIL_SUCCESS',
                request.path,
                additional_info=f"Updated language progress ID: {progress_id}"
            )

        return response

    @swagger_auto_schema(
        operation_description="Delete language progress",
        responses={204: 'No Content'}
    )
    def delete(self, request, *args, **kwargs):
        progress_id = kwargs.get('pk')
        self.log_progress_request(
            request,
            'DELETE_ATTEMPT',
            request.path,
            additional_info=f"Deleting language progress ID: {progress_id}"
        )

        response = super().delete(request, *args, **kwargs)

        if response.status_code == 204:
            self.log_progress_request(
                request,
                'DELETE_SUCCESS',
                request.path,
                additional_info=f"Deleted language progress ID: {progress_id}"
            )

        return response


class WordsProgressListCreateView(ProgressLoggingMixin, generics.ListCreateAPIView):
    """List and create words progress for authenticated user"""
    serializer_class = WordsProgressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Handle Swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return WordsProgress.objects.none()

        queryset = WordsProgress.objects.filter(user=self.request.user)

        # Filter by status if provided
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Filter by target language if provided
        target_language = self.request.query_params.get('target_language', None)
        if target_language:
            queryset = queryset.filter(target_language__code=target_language)

        # Filter by word language if provided
        word_language = self.request.query_params.get('word_language', None)
        if word_language:
            queryset = queryset.filter(word__language__code=word_language)

        # Filter words due for review
        due_for_review = self.request.query_params.get('due_for_review', None)
        if due_for_review and due_for_review.lower() == 'true':
            from django.utils import timezone
            queryset = queryset.filter(
                next_review__lte=timezone.now(),
                status__in=['new', 'learning']
            )

        # Log queryset info
        if hasattr(self, 'request'):
            self.log_queryset_info(self.request, queryset, 'words-progress-list')

        return queryset.select_related('word', 'word__language', 'target_language', 'word__part_of_speech')

    @swagger_auto_schema(
        operation_description="Get user's words learning progress",
        manual_parameters=[
            openapi.Parameter('status', openapi.IN_QUERY, description="Filter by status (new, learning, learned, mastered)", type=openapi.TYPE_STRING),
            openapi.Parameter('target_language', openapi.IN_QUERY, description="Filter by target language code", type=openapi.TYPE_STRING),
            openapi.Parameter('word_language', openapi.IN_QUERY, description="Filter by word language code", type=openapi.TYPE_STRING),
            openapi.Parameter('due_for_review', openapi.IN_QUERY, description="Filter words due for review (true/false)", type=openapi.TYPE_BOOLEAN),
        ],
        responses={200: WordsProgressSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)

        # Log additional info about the response
        result_count = len(response.data) if hasattr(response, 'data') and response.data else 0

        # Log filter information
        filters_applied = []
        for param in ['status', 'target_language', 'word_language', 'due_for_review']:
            if request.query_params.get(param):
                filters_applied.append(f"{param}={request.query_params.get(param)}")

        filter_info = f"Filters: {', '.join(filters_applied)}" if filters_applied else "No filters"

        self.log_progress_request(
            request,
            'GET_RESULT',
            request.path,
            additional_info=f"Returned {result_count} words progress entries. {filter_info}"
        )

        return response

    @swagger_auto_schema(
        operation_description="Create new words progress entry",
        responses={
            201: WordsProgressSerializer,
            400: 'Bad Request'
        }
    )
    def post(self, request, *args, **kwargs):
        # Log creation attempt details
        word_id = request.data.get('word') if hasattr(request, 'data') else None
        target_language_id = request.data.get('target_language') if hasattr(request, 'data') else None

        self.log_progress_request(
            request,
            'CREATE_ATTEMPT',
            request.path,
            additional_info=f"Creating words progress for word_id: {word_id}, target_language_id: {target_language_id}"
        )

        response = super().post(request, *args, **kwargs)

        # Log creation result
        if response.status_code == 201:
            created_id = response.data.get('id') if hasattr(response, 'data') else None
            word_text = response.data.get('word_text') if hasattr(response, 'data') else 'Unknown'
            self.log_progress_request(
                request,
                'CREATE_SUCCESS',
                request.path,
                additional_info=f"Created words progress with ID: {created_id} for word: '{word_text}'"
            )

        return response


class WordsProgressDetailView(ProgressLoggingMixin, generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete specific words progress"""
    serializer_class = WordsProgressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Handle Swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return WordsProgress.objects.none()
        return WordsProgress.objects.filter(user=self.request.user).select_related(
            'word', 'word__language', 'target_language', 'word__part_of_speech'
        )

    @swagger_auto_schema(
        operation_description="Get specific words progress",
        responses={200: WordsProgressSerializer}
    )
    def get(self, request, *args, **kwargs):
        progress_id = kwargs.get('pk')
        self.log_progress_request(
            request,
            'GET_DETAIL_ATTEMPT',
            request.path,
            additional_info=f"Retrieving words progress ID: {progress_id}"
        )

        response = super().get(request, *args, **kwargs)

        if response.status_code == 200:
            word_text = response.data.get('word_text') if hasattr(response, 'data') else 'Unknown'
            status = response.data.get('status') if hasattr(response, 'data') else 'Unknown'
            self.log_progress_request(
                request,
                'GET_DETAIL_SUCCESS',
                request.path,
                additional_info=f"Retrieved progress for word: '{word_text}', status: {status}"
            )

        return response

    @swagger_auto_schema(
        operation_description="Update words progress",
        responses={200: WordsProgressSerializer}
    )
    def patch(self, request, *args, **kwargs):
        progress_id = kwargs.get('pk')

        # Log what fields are being updated
        update_fields = list(request.data.keys()) if hasattr(request, 'data') else []

        self.log_progress_request(
            request,
            'UPDATE_DETAIL_ATTEMPT',
            request.path,
            additional_info=f"Updating words progress ID: {progress_id}, fields: {update_fields}"
        )

        response = super().patch(request, *args, **kwargs)

        if response.status_code == 200:
            word_text = response.data.get('word_text') if hasattr(response, 'data') else 'Unknown'
            new_status = response.data.get('status') if hasattr(response, 'data') else 'Unknown'
            self.log_progress_request(
                request,
                'UPDATE_DETAIL_SUCCESS',
                request.path,
                additional_info=f"Updated words progress ID: {progress_id} for word: '{word_text}', new status: {new_status}"
            )

        return response

    @swagger_auto_schema(
        operation_description="Delete words progress",
        responses={204: 'No Content'}
    )
    def delete(self, request, *args, **kwargs):
        progress_id = kwargs.get('pk')

        # Try to get word info before deletion
        try:
            progress = self.get_object()
            word_text = progress.word.text if progress and progress.word else 'Unknown'
        except:
            word_text = 'Unknown'

        self.log_progress_request(
            request,
            'DELETE_ATTEMPT',
            request.path,
            additional_info=f"Deleting words progress ID: {progress_id} for word: '{word_text}'"
        )

        response = super().delete(request, *args, **kwargs)

        if response.status_code == 204:
            self.log_progress_request(
                request,
                'DELETE_SUCCESS',
                request.path,
                additional_info=f"Deleted words progress ID: {progress_id} for word: '{word_text}'"
            )

        return response


class WordsProgressBulkUpdateView(ProgressLoggingMixin, generics.GenericAPIView):
    """Bulk update words progress (for spaced repetition reviews)"""
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Bulk update words progress after review session",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'updates': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'correct': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                            'status': openapi.Schema(type=openapi.TYPE_STRING, enum=['new', 'learning', 'learned', 'mastered']),
                            'interval': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'next_review': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                        },
                        required=['id', 'correct']
                    )
                )
            },
            required=['updates']
        ),
        responses={
            200: openapi.Response('Bulk update successful'),
            400: 'Bad Request'
        }
    )
    def post(self, request, *args, **kwargs):
        """Bulk update words progress after review session"""
        updates = request.data.get('updates', [])

        # Log bulk update attempt
        self.log_progress_request(
            request,
            'BULK_UPDATE_ATTEMPT',
            request.path,
            additional_info=f"Processing {len(updates)} bulk updates"
        )

        if not updates:
            self.log_progress_request(
                request,
                'BULK_UPDATE_ERROR',
                request.path,
                additional_info="No updates provided in request",
                error="No updates provided"
            )
            return Response({'error': 'No updates provided'}, status=status.HTTP_400_BAD_REQUEST)

        updated_count = 0
        errors = []
        correct_answers = 0
        incorrect_answers = 0
        status_changes = {}

        for update_data in updates:
            try:
                progress_id = update_data.get('id')
                if not progress_id:
                    errors.append({'error': 'Missing id in update data', 'data': update_data})
                    continue

                # Get the progress entry
                try:
                    progress = WordsProgress.objects.get(id=progress_id, user=request.user)
                    word_text = progress.word.text if progress.word else f"ID:{progress_id}"
                except WordsProgress.DoesNotExist:
                    errors.append({'error': f'Words progress with id {progress_id} not found'})
                    continue

                # Track old status for logging
                old_status = progress.status

                # Update review count
                progress.review_count += 1

                # Track correct/incorrect answers
                is_correct = update_data.get('correct', False)
                if is_correct:
                    progress.correct_count += 1
                    correct_answers += 1
                else:
                    incorrect_answers += 1

                # Update other fields if provided
                if 'status' in update_data:
                    new_status = update_data['status']
                    progress.status = new_status

                    # Track status changes
                    if old_status != new_status:
                        status_key = f"{old_status}->{new_status}"
                        status_changes[status_key] = status_changes.get(status_key, 0) + 1

                if 'interval' in update_data:
                    progress.interval = update_data['interval']

                if 'next_review' in update_data:
                    from django.utils.dateparse import parse_datetime
                    next_review = parse_datetime(update_data['next_review'])
                    if next_review:
                        progress.next_review = next_review

                # Set date_learned if status is learned or mastered
                if progress.status in ['learned', 'mastered'] and not progress.date_learned:
                    from django.utils import timezone
                    progress.date_learned = timezone.now().date()

                progress.save()
                updated_count += 1

                # Log individual update for important status changes
                if old_status != progress.status and progress.status in ['learned', 'mastered']:
                    self.log_progress_request(
                        request,
                        'BULK_UPDATE_MILESTONE',
                        request.path,
                        additional_info=f"Word '{word_text}' (ID: {progress_id}) advanced to {progress.status}"
                    )

            except Exception as e:
                error_msg = f"Failed to update progress ID {progress_id}: {str(e)}"
                errors.append({'error': str(e), 'data': update_data})
                self.log_progress_request(
                    request,
                    'BULK_UPDATE_ITEM_ERROR',
                    request.path,
                    additional_info=error_msg,
                    error=str(e)
                )

        # Prepare response data
        response_data = {
            'updated_count': updated_count,
            'total_requested': len(updates)
        }

        if errors:
            response_data['errors'] = errors

        # Log bulk update completion with detailed statistics
        status_changes_str = ", ".join([f"{k}: {v}" for k, v in status_changes.items()]) if status_changes else "None"

        completion_info = (
            f"Bulk update completed: {updated_count}/{len(updates)} successful, "
            f"Correct answers: {correct_answers}, Incorrect: {incorrect_answers}, "
            f"Status changes: {status_changes_str}, Errors: {len(errors)}"
        )

        if errors:
            self.log_progress_request(
                request,
                'BULK_UPDATE_COMPLETED_WITH_ERRORS',
                request.path,
                additional_info=completion_info
            )
        else:
            self.log_progress_request(
                request,
                'BULK_UPDATE_SUCCESS',
                request.path,
                additional_info=completion_info
            )

        return Response(response_data, status=status.HTTP_200_OK)


class WordsLearnedTodayView(ProgressLoggingMixin, generics.GenericAPIView):
    """Get count of words learned today"""
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get count of words learned today",
        responses={
            200: openapi.Response(
                'Words learned today count',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
                        'words_learned_today': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'words_mastered_today': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'total_learned_today': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'breakdown_by_language': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'language_code': openapi.Schema(type=openapi.TYPE_STRING),
                                    'language_name': openapi.Schema(type=openapi.TYPE_STRING),
                                    'new_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'learning_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'learned_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'mastered_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'total_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                                }
                            )
                        )
                    }
                )
            )
        }
    )
    def get(self, request, *args, **kwargs):
        """Get statistics for words learned today"""
        from django.utils import timezone
        from django.db.models import Count, Q

        # Log request attempt
        self.log_progress_request(
            request,
            'WORDS_LEARNED_TODAY_ATTEMPT',
            request.path,
            additional_info="Retrieving today's learned words statistics"
        )

        try:
            today = timezone.now().date()
            user = request.user

            # Debug: Log the date we're filtering by
            print(f"[DEBUG] Filtering by date: {today}")
            print(f"[DEBUG] User: {user.email} (ID: {user.id})")

            # Get words learned today
            words_learned_today = WordsProgress.objects.filter(
                user=user,
                date_learned=today,
                status__in=['learned', 'mastered']
            ).select_related('word', 'word__language', 'target_language')

            # Debug: Check total count before status filtering
            all_words_today = WordsProgress.objects.filter(
                user=user,
                date_learned=today
            )
            print(f"[DEBUG] Total words with date_learned={today}: {all_words_today.count()}")
            print(f"[DEBUG] Words with learned/mastered status: {words_learned_today.count()}")

            # Debug: Show some sample records
            for progress in words_learned_today[:5]:
                print(f"[DEBUG] Word: {progress.word.word}, Status: {progress.status}, Date: {progress.date_learned}")

            # Count by status
            new_count = words_learned_today.filter(status='nes').count()
            learning_count = words_learned_today.filter(status='learning').count()
            learned_count = words_learned_today.filter(status='learned').count()
            mastered_count = words_learned_today.filter(status='mastered').count()
            total_count = learned_count + mastered_count

            print(f"[DEBUG] Learned: {learned_count}, Mastered: {mastered_count}, Total: {total_count}")

            # Breakdown by language
            language_breakdown = []
            language_stats = words_learned_today.values(
                'target_language__code',
                'target_language__name_english'
            ).annotate(
                new_count=Count('id', filter=Q(status='new')),
                learned_count=Count('id', filter=Q(status='learned')),
                learning_count=Count('id', filter=Q(status='learning')),
                mastered_count=Count('id', filter=Q(status='mastered')),
                total_count=Count('id')
            ).order_by('-total_count')

            for lang_stat in language_stats:
                if lang_stat['total_count'] > 0:  # Only include languages with learned words
                    language_breakdown.append({
                        'language_code': lang_stat['target_language__code'],
                        'language_name': lang_stat['target_language__name_english'],
                        'new_count': lang_stat['new_count'],
                        'learning_count': lang_stat['learning_count'],
                        'learned_count': lang_stat['learned_count'],
                        'mastered_count': lang_stat['mastered_count'],
                        'total_count': lang_stat['total_count']
                    })

            response_data = {
                'date': today.isoformat(),
                'words_learned_today': learned_count,
                'words_mastered_today': mastered_count,
                'total_learned_today': total_count,
                'breakdown_by_language': language_breakdown
            }

            # Log successful response with statistics
            stats_info = (
                f"Today's stats: {total_count} total words "
                f"({learned_count} learned, {mastered_count} mastered), "
                f"{len(language_breakdown)} languages involved"
            )

            self.log_progress_request(
                request,
                'WORDS_LEARNED_TODAY_SUCCESS',
                request.path,
                additional_info=stats_info,
                response_status=200
            )

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            # Log error
            error_message = f"Failed to retrieve today's learned words statistics: {str(e)}"
            self.log_progress_request(
                request,
                'WORDS_LEARNED_TODAY_ERROR',
                request.path,
                error=e,
                response_status=500
            )

            return Response(
                {'error': 'Failed to retrieve statistics'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class QuizProgressListCreateView(ProgressLoggingMixin, generics.ListCreateAPIView):
    """List and create quiz progress for authenticated user"""
    serializer_class = QuizProgressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Handle Swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return QuizProgress.objects.none()

        queryset = QuizProgress.objects.filter(user=self.request.user)

        # Filter by language if provided
        language_filter = self.request.query_params.get('language', None)
        if language_filter:
            queryset = queryset.filter(language__code=language_filter)

        # Log queryset info
        if hasattr(self, 'request'):
            self.log_queryset_info(self.request, queryset, 'quiz-progress-list')

        return queryset.select_related('language')

    @swagger_auto_schema(
        operation_description="Get user's quiz progress",
        manual_parameters=[
            openapi.Parameter('language', openapi.IN_QUERY, description="Filter by language code", type=openapi.TYPE_STRING),
        ],
        responses={200: QuizProgressSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)

        # Log additional info about the response
        result_count = len(response.data) if hasattr(response, 'data') and response.data else 0
        language_filter = request.query_params.get('language', 'all')

        self.log_progress_request(
            request,
            'GET_RESULT',
            request.path,
            additional_info=f"Returned {result_count} quiz progress entries for language: {language_filter}"
        )

        return response

    @swagger_auto_schema(
        operation_description="Create new quiz progress entry",
        responses={
            201: QuizProgressSerializer,
            400: 'Bad Request'
        }
    )
    def post(self, request, *args, **kwargs):
        # Log creation attempt details
        language_id = request.data.get('language_id') if hasattr(request, 'data') else None
        total_questions = request.data.get('total_questions') if hasattr(request, 'data') else None
        correct_answers = request.data.get('correct_answers') if hasattr(request, 'data') else None

        self.log_progress_request(
            request,
            'CREATE_ATTEMPT',
            request.path,
            additional_info=f"Creating quiz progress for language_id: {language_id}, questions: {total_questions}, correct: {correct_answers}"
        )

        response = super().post(request, *args, **kwargs)

        # Log creation result
        if response.status_code == 201:
            created_id = response.data.get('id') if hasattr(response, 'data') else None
            accuracy = response.data.get('accuracy_percentage') if hasattr(response, 'data') else 'Unknown'
            self.log_progress_request(
                request,
                'CREATE_SUCCESS',
                request.path,
                additional_info=f"Created quiz progress with ID: {created_id}, accuracy: {accuracy}%"
            )

        return response


class QuizStatsView(ProgressLoggingMixin, generics.GenericAPIView):
    """Get quiz statistics for authenticated user"""
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get quiz statistics by language",
        manual_parameters=[
            openapi.Parameter('language', openapi.IN_QUERY, description="Filter by language code", type=openapi.TYPE_STRING),
        ],
        responses={
            200: openapi.Response(
                'Quiz statistics',
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'language': openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'code': openapi.Schema(type=openapi.TYPE_STRING),
                                    'name_english': openapi.Schema(type=openapi.TYPE_STRING),
                                    'name_native': openapi.Schema(type=openapi.TYPE_STRING),
                                }
                            ),
                            'total_questions': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'average_accuracy': openapi.Schema(type=openapi.TYPE_NUMBER),
                            'quiz_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                        }
                    )
                )
            )
        }
    )
    def get(self, request, *args, **kwargs):
        """Get quiz statistics grouped by language"""
        from django.db.models import Sum, Avg, Count
        from languages.serializers import LanguageSerializer

        # Log request attempt
        language_filter = request.query_params.get('language', None)
        self.log_progress_request(
            request,
            'QUIZ_STATS_ATTEMPT',
            request.path,
            additional_info=f"Retrieving quiz statistics for language: {language_filter or 'all'}"
        )

        try:
            user = request.user
            queryset = QuizProgress.objects.filter(user=user)

            # Apply language filter if provided
            if language_filter:
                queryset = queryset.filter(language__code=language_filter)

            # Group by language and calculate statistics
            stats = queryset.values('language').annotate(
                total_questions=Sum('total_questions'),
                total_correct=Sum('correct_answers'),
                quiz_count=Count('id')
            ).order_by('-total_questions')

            # Calculate average accuracy and prepare response data
            response_data = []
            for stat in stats:
                if stat['total_questions'] > 0:
                    average_accuracy = round((stat['total_correct'] / stat['total_questions']) * 100, 2)
                else:
                    average_accuracy = 0.0

                # Get language object for serialization
                from languages.models import Language
                language = Language.objects.get(id=stat['language'])

                response_data.append({
                    'language': LanguageSerializer(language).data,
                    'total_questions': stat['total_questions'],
                    'average_accuracy': average_accuracy,
                    'quiz_count': stat['quiz_count']
                })

            # Log successful response with statistics
            total_languages = len(response_data)
            total_quizzes = sum(item['quiz_count'] for item in response_data)
            total_questions = sum(item['total_questions'] for item in response_data)

            stats_info = (
                f"Quiz stats: {total_languages} languages, "
                f"{total_quizzes} total quizzes, "
                f"{total_questions} total questions"
            )

            self.log_progress_request(
                request,
                'QUIZ_STATS_SUCCESS',
                request.path,
                additional_info=stats_info,
                response_status=200
            )

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            # Log error
            error_message = f"Failed to retrieve quiz statistics: {str(e)}"
            self.log_progress_request(
                request,
                'QUIZ_STATS_ERROR',
                request.path,
                error=e,
                response_status=500
            )

            return Response(
                {'error': 'Failed to retrieve quiz statistics'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class WordsLearnedStatsView(ProgressLoggingMixin, generics.GenericAPIView):
    """Get extended statistics for words learned over different periods"""
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get words learned statistics for different time periods",
        manual_parameters=[
            openapi.Parameter(
                'period',
                openapi.IN_QUERY,
                description="Time period (today, week, month, year, all)",
                type=openapi.TYPE_STRING,
                default='today'
            ),
            openapi.Parameter(
                'language',
                openapi.IN_QUERY,
                description="Filter by target language code",
                type=openapi.TYPE_STRING
            ),
        ],
        responses={
            200: openapi.Response(
                'Words learned statistics',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'period': openapi.Schema(type=openapi.TYPE_STRING),
                        'start_date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
                        'end_date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
                        'words_learned': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'words_mastered': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'total_words': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'daily_breakdown': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
                                    'learned': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'mastered': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'total': openapi.Schema(type=openapi.TYPE_INTEGER),
                                }
                            )
                        ),
                        'language_breakdown': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'language_code': openapi.Schema(type=openapi.TYPE_STRING),
                                    'language_name': openapi.Schema(type=openapi.TYPE_STRING),
                                    'new_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'learning_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'learned_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'mastered_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'total_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                                }
                            )
                        )
                    }
                )
            ),
            400: 'Bad Request'
        }
    )
    def get(self, request, *args, **kwargs):
        """Get extended statistics for words learned over different periods"""
        from django.utils import timezone
        from django.db.models import Count, Q
        from datetime import timedelta

        period = request.query_params.get('period', 'today').lower()
        language_filter = request.query_params.get('language', None)

        # Log request attempt
        self.log_progress_request(
            request,
            'WORDS_STATS_ATTEMPT',
            request.path,
            additional_info=f"Retrieving words statistics for period: {period}, language: {language_filter or 'all'}"
        )

        try:
            today = timezone.now().date()
            user = request.user

            # Calculate date range based on period
            if period == 'today':
                start_date = today
                end_date = today
            elif period == 'week':
                start_date = today - timedelta(days=today.weekday())  # Start of current week
                end_date = today
            elif period == 'month':
                start_date = today.replace(day=1)  # Start of current month
                end_date = today
            elif period == 'year':
                start_date = today.replace(month=1, day=1)  # Start of current year
                end_date = today
            elif period == 'all':
                start_date = None
                end_date = today
            else:
                return Response(
                    {'error': 'Invalid period. Use: today, week, month, year, or all'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Debug logging
            print(f"[DEBUG] Period: {period}, Start: {start_date}, End: {end_date}")
            print(f"[DEBUG] Language filter: {language_filter}")

            # Base queryset
            queryset = WordsProgress.objects.filter(
                user=user,
                date_learned__isnull=False
            )

            # Debug: Check base queryset count
            print(f"[DEBUG] Base queryset count (all learned/mastered with date): {queryset.count()}")

            # Apply date filter
            if start_date:
                queryset = queryset.filter(date_learned__gte=start_date)
            queryset = queryset.filter(date_learned__lte=end_date)

            # Debug: Check after date filtering
            print(f"[DEBUG] After date filtering: {queryset.count()}")

            # Apply language filter if provided
            if language_filter:
                queryset = queryset.filter(target_language__code=language_filter)
                print(f"[DEBUG] After language filtering: {queryset.count()}")

            queryset = queryset.select_related('word', 'word__language', 'target_language')

            # Count by status
            new_count = queryset.filter(status='new').count()
            learning_count = queryset.filter(status='learning').count()
            learned_count = queryset.filter(status='learned').count()
            mastered_count = queryset.filter(status='mastered').count()
            total_count = learned_count + mastered_count

            print(f"[DEBUG] Final counts - Learned: {learned_count}, Mastered: {mastered_count}, Total: {total_count}")

            # Daily breakdown (only for periods with reasonable number of days)
            daily_breakdown = []
            if period in ['today', 'week', 'month'] or (period == 'year' and start_date):
                daily_stats = queryset.values('date_learned').annotate(
                    new=Count('id', filter=Q(status='new')),
                    learning=Count('id', filter=Q(status='learning')),
                    learned=Count('id', filter=Q(status='learned')),
                    mastered=Count('id', filter=Q(status='mastered')),
                    total=Count('id')
                ).order_by('date_learned')

                daily_breakdown = [
                    {
                        'date': stat['date_learned'].isoformat(),  # Fixed: added .isoformat()
                        'new': stat['new'],
                        'learning': stat['learning'],
                        'learned': stat['learned'],
                        'mastered': stat['mastered'],
                        'total': stat['total']
                    }
                    for stat in daily_stats
                ]

            # Language breakdown
            language_breakdown = []
            language_stats = queryset.values(
                'target_language__code',
                'target_language__name_english'
            ).annotate(
                new_count=Count('id', filter=Q(status='new')),
                learning_count=Count('id', filter=Q(status='learning')),
                learned_count=Count('id', filter=Q(status='learned')),
                mastered_count=Count('id', filter=Q(status='mastered')),
                total_count=Count('id')
            ).order_by('-total_count')

            for lang_stat in language_stats:
                if lang_stat['total_count'] > 0:
                    language_breakdown.append({
                        'language_code': lang_stat['target_language__code'],
                        'language_name': lang_stat['target_language__name_english'],
                        'new_count': lang_stat['new_count'],
                        'learning_count': lang_stat['learning_count'],
                        'learned_count': lang_stat['learned_count'],
                        'mastered_count': lang_stat['mastered_count'],
                        'total_count': lang_stat['total_count']
                    })

            response_data = {
                'period': period,
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat(),
                'words_new': new_count,
                'words_learning': learning_count,
                'words_learned': learned_count,
                'words_mastered': mastered_count,
                'total_words': total_count,
                'daily_breakdown': daily_breakdown,
                'language_breakdown': language_breakdown
            }

            # Log successful response with statistics
            stats_info = (
                f"Stats for {period}: {total_count} total words "
                f"({learned_count} learned, {mastered_count} mastered), "
                f"{len(language_breakdown)} languages, "
                f"{len(daily_breakdown)} days with activity"
            )

            self.log_progress_request(
                request,
                'WORDS_STATS_SUCCESS',
                request.path,
                additional_info=stats_info,
                response_status=200
            )

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            # Log error
            error_message = f"Failed to retrieve words statistics for period {period}: {str(e)}"
            self.log_progress_request(
                request,
                'WORDS_STATS_ERROR',
                request.path,
                error=e,
                response_status=500
            )

            return Response(
                {'error': 'Failed to retrieve statistics'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class QuizProgressDetailView(ProgressLoggingMixin, generics.RetrieveAPIView):
    """Retrieve specific quiz progress by ID"""
    serializer_class = QuizProgressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Handle Swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return QuizProgress.objects.none()
        return QuizProgress.objects.filter(user=self.request.user).select_related('language')

    @swagger_auto_schema(
        operation_description="Get specific quiz progress by ID",
        responses={
            200: QuizProgressSerializer,
            404: 'Quiz not found'
        }
    )
    def get(self, request, *args, **kwargs):
        quiz_id = kwargs.get('pk')
        self.log_progress_request(
            request,
            'GET_QUIZ_DETAIL_ATTEMPT',
            request.path,
            additional_info=f"Retrieving quiz progress ID: {quiz_id}"
        )

        try:
            response = super().get(request, *args, **kwargs)

            if response.status_code == 200:
                quiz_data = response.data
                language_name = quiz_data.get('language', {}).get('name_english', 'Unknown')
                accuracy = quiz_data.get('accuracy_percentage', 'Unknown')
                total_questions = quiz_data.get('total_questions', 'Unknown')
                correct_answers = quiz_data.get('correct_answers', 'Unknown')

                self.log_progress_request(
                    request,
                    'GET_QUIZ_DETAIL_SUCCESS',
                    request.path,
                    additional_info=f"Retrieved quiz ID: {quiz_id}, Language: {language_name}, Score: {correct_answers}/{total_questions} ({accuracy}%)"
                )

            return response

        except Exception as e:
            self.log_progress_request(
                request,
                'GET_QUIZ_DETAIL_ERROR',
                request.path,
                additional_info=f"Failed to retrieve quiz ID: {quiz_id}",
                error=e,
                response_status=500
            )
            raise
