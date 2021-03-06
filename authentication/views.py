from random import choice
import jwt

from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from decouple import config
from dj_rest_auth.registration.views import SocialLoginView
from django.conf import settings
from django.contrib.auth import authenticate
from django.shortcuts import get_list_or_404
from django.urls import reverse
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from src.permissions import IsOwnerOrReadOnly
from src.utils import Utils, otp_session
from src.utils import Utils
from drf_yasg.utils import swagger_auto_schema

from .models import User
from .permissions import PostReadAllPermission
from .serializers import (
    CustomerRegistrationSerializer,
    CustomerSerializer,
    ServiceProviderSerializer,
    ServiceProviderRegistrationSerializer,
    TokenRefreshSerializer,
    UpdatePhoneSerializer,
    VerificationSerializer,
    UserSerializer,
    LoginSerializer,
)

http_protocol = config("HTTP")


class CustomerRegisterGetAll(APIView):
    permission_classes = (PostReadAllPermission,)
    serializer_class = CustomerRegistrationSerializer

    def get(self, request):
        users_objs = get_list_or_404(User, role="customer")
        users_serilizer = CustomerRegistrationSerializer(users_objs, many=True)
        data = {
            "message": "Successfully retrieved customers",
            "data": users_serilizer.data,
        }
        return Response(data, status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=serializer_class)
    def post(self, request):
        serializer = CustomerRegistrationSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()

            user_data = serializer.data
            user = User.objects.get(email=user_data["email"])
            token = RefreshToken.for_user(user).access_token
            relative_link = reverse("verify_email")
            current_site = request.get_host()
            absolute_url = (
                f"{http_protocol}{current_site}{relative_link}?token={str(token)}"
            )
            email_body = f"""
                        <h2>Hi, <small>{user.first_name}</small></h2>    
                        <h4>Use the link below to verify your email.</h4>
                        <p>{absolute_url}</p>
                        """

            data = {
                "email_subject": "Verify your email",
                "email_body": email_body,
                "to_email": user.email,
            }

            # result a message id, if sent successfully
            Utils.sending_email(data)

            return_data = dict(serializer.data)
            return_data["verification_link"] = absolute_url

            return Response(return_data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomerRetrieveUpdateDelete(APIView):
    serializer_class = CustomerSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self, id):
        try:
            return User.objects.get(pk=id)
        except User.DoesNotExist:
            return None

    def get(self, request, id):

        if customer := self.get_object(id):
            serializer = CustomerSerializer(customer)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(
                {"message": "Invalid User ID"}, status=status.HTTP_404_NOT_FOUND
            )

    def put(self, request, id):
        if customer := self.get_object(id):
            serializer = CustomerSerializer(customer, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(
                {"message": "Invalid User ID", "status": status.HTTP_404_NOT_FOUND}
            )

    def delete(self, request, id):
        if customer := self.get_object(id):
            customer.delete()
            return Response(
                {
                    "message": "User deleted successfully",
                    "status": status.HTTP_204_NO_CONTENT,
                }
            )
        else:
            return Response(
                {"message": "Invalid User ID", "status": status.HTTP_404_NOT_FOUND}
            )


class ServiceProviderRegister(APIView):
    serializer_class = ServiceProviderRegistrationSerializer
    # permission_classes = (PostReadAllPermission,)

    def get(self, request):
        users_objs = get_list_or_404(User, user__role="service_provider")
        users_serilizer = ServiceProviderRegistrationSerializer(users_objs, many=True)
        data = {
            "message": "Successfully retrieved sp-customers",
            "data": users_serilizer.data,
        }
        return Response(data, status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=serializer_class)
    def post(self, request):
        serializer = ServiceProviderRegistrationSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            user_data = serializer.data

            user = User.objects.get(email=user_data["user"]["email"])

            token = RefreshToken.for_user(user).access_token

            relative_link = reverse("verify_email")

            current_site = request.get_host()

            absolute_url = (
                f"{http_protocol}{current_site}{relative_link}?token={str(token)}"
            )

            email_body = f"""
                        <h2>Hi, <small>{user.first_name}</small></h2>    
                        <h4>Use the link below to verify your email.</h4>
                        <p>{absolute_url}</p>

                        """
            data = {
                "email_subject": "Verify your email",
                "email_body": email_body,
                "to_email": user.email,
            }

            # result a message id, if sent successfully
            Utils.sending_email(data)

            return_data = dict(serializer.data)
            return_data["verification_link"] = absolute_url

            return Response(return_data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ServiceProviderRetrieveUpdateDelete(APIView):
    serializer_class = ServiceProviderSerializer
    # permission_classes = (IsAuthenticated,)

    def get_object(self, id):
        try:
            return User.objects.get(pk=id)
        except User.DoesNotExist:
            return None

    def get(self, request, id):

        if service_provider := self.get_object(id):
            serializer = ServiceProviderSerializer(service_provider)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(
                {"message": "Invalid User ID", "status": status.HTTP_404_NOT_FOUND}
            )

    # not functioning yet
    def put(self, request, id):
        if service_provider := self.get_object(id):
            serializer = ServiceProviderSerializer(service_provider, data=request.data)

            if serializer.is_valid():

                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(
                {"message": "Invalid User ID", "status": status.HTTP_404_NOT_FOUND}
            )

    def delete(self, request, id):

        if service_provider := self.get_object(id):
            service_provider.delete()
            return Response(
                {
                    "message": "User deleted successfully",
                    "status": status.HTTP_204_NO_CONTENT,
                }
            )
        else:
            return Response(
                {"message": "Invalid User ID", "status": status.HTTP_404_NOT_FOUND}
            )


class VerifyEmail(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        token = request.GET.get("token")
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user = User.objects.get(id=payload["user_id"])

            if not user.is_verified:
                user._is_verified = True
                user.email_verification = True
                user.save()

            return Response(
                {"email": "user email verified successfully"}, status=status.HTTP_200_OK
            )
        except jwt.ExpiredSignatureError:
            return Response(
                {"error": "Verification link expired"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except jwt.exceptions.DecodeError:
            return Response(
                {"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST
            )


class VerifyPhone(APIView):
    serializer_class = VerificationSerializer
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(request_body=serializer_class)
    def post(self, request):

        otp_code = request.data.get("otp")
        user = User.objects.get(id=request.user.id)
        phone_number = user["phone_number"]

        try:
            if not user.phone_verification:
                if not "code" in request.session.keys():
                    sent_otp = otp_session(request, phone_number)
                    if sent_otp:
                        return Response(
                            {
                                "status": status.HTTP_200_OK,
                                "message": "OTP sent successfully",
                            }
                        )
                    return Response(
                        {
                            "status": status.HTTP_400_BAD_REQUEST,
                            "message": "Sending OTP Error",
                        }
                    )
                else:
                    if otp_code:
                        if str(otp_code) == str(request.session["code"]):
                            user.phone_verification = True
                            user.save()

                            request.session.clear()
                            return Response(
                                {
                                    "status": status.HTTP_200_OK,
                                    "message": "OTP Code Verified",
                                }
                            )
                        request.session.clear()
                        return Response(
                            {
                                "status": status.HTTP_400_BAD_REQUEST,
                                "message": "OTP Incorrect!",
                            }
                        )
                    request.session.clear()
                    return Response(
                        {
                            "status": status.HTTP_400_BAD_REQUEST,
                            "message": "Invalid OTP!",
                        }
                    )
            return Response(
                {
                    "status": status.HTTP_403_FORBIDDEN,
                    "message": "Phone number already validated",
                }
            )
        except jwt.ExpiredSignatureError:
            return Response(
                {
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Verification link expired",
                }
            )
        except jwt.exceptions.DecodeError:
            return Response(
                {
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid token",
                }
            )


class UpdatePhone(APIView):
    serializer_class = UpdatePhoneSerializer
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(request_body=serializer_class)
    def post(self, request):

        otp_code, new_number = request.data.get("otp"), request.data.get("number")
        user = User.objects.get(id=request.user.id)
        try:
            if not User.objects.filter(phone_number__iexact=new_number).exists():

                if not "code" in request.session.keys():
                    sent_otp = otp_session(request, new_number)
                    if sent_otp:
                        return Response(
                            {
                                "status": status.HTTP_200_OK,
                                "message": "OTP sent successfully",
                            }
                        )
                    return Response(
                        {
                            "status": status.HTTP_400_BAD_REQUEST,
                            "message": "Sending OTP Error",
                        }
                    )

                else:
                    if otp_code:
                        if str(otp_code) == str(request.session["code"]):
                            user.phone_verification = True
                            user.phone_number = new_number
                            user.save()

                            request.session.clear()
                            return Response(
                                {
                                    "status": status.HTTP_200_OK,
                                    "message": "OTP Code Verified",
                                }
                            )
                        request.session.clear()
                        return Response(
                            {
                                "status": status.HTTP_400_BAD_REQUEST,
                                "message": "OTP Incorrect!",
                            }
                        )
                    request.session.clear()
                    return Response(
                        {
                            "status": status.HTTP_400_BAD_REQUEST,
                            "message": "Invalid OTP!",
                        }
                    )

            return Response(
                {
                    "status": status.HTTP_403_FORBIDDEN,
                    "message": "Phone number already Exist",
                }
            )

        except jwt.ExpiredSignatureError:
            return Response(
                {
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Verification link expired",
                }
            )
        except jwt.exceptions.DecodeError:
            return Response(
                {
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid token",
                }
            )


class CustomerLogin(APIView):
    serializer_class = LoginSerializer

    def post(self, request):
        if "email" not in request.data.keys() or "password" not in request.data.keys():
            return Response(
                {
                    "code": 400,
                    "status": "Failed",
                    "message": "Please enter your email address and password.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            user = User.objects.get(email=request.POST["email"])
            if user.role == "customer":
                response = Utils.create_token(
                    email=request.POST["email"], password=request.POST["password"]
                )
                if "error" in response.keys():
                    return Response(
                        {"code": 400, "status": "Failed", "message": response},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                else:
                    return Response(
                        {"code": 200, "status": "Success", "message": response},
                        status=status.HTTP_200_OK,
                    )
            else:
                return Response(
                    {
                        "code": 400,
                        "status": "Failed",
                        "message": "You're not a customer. Try the logging in as a service provider",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )


class ServiceProviderLogin(APIView):
    serializer_class = LoginSerializer

    def post(self, request):
        if "email" not in request.data.keys() or "password" not in request.data.keys():
            return Response(
                {
                    "code": 400,
                    "status": "Failed",
                    "message": "Please enter your email address and password.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            user = User.objects.get(email=request.POST["email"])
            if user.role == "service_provider":
                response = Utils.create_token(
                    email=request.POST["email"], password=request.POST["password"]
                )
                if "error" in response.keys():
                    return Response(
                        {"code": 400, "status": "Failed", "message": response},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                else:
                    return Response(
                        {"code": 200, "status": "Success", "message": response},
                        status=status.HTTP_200_OK,
                    )
            else:
                return Response(
                    {
                        "code": 400,
                        "status": "Failed",
                        "message": "You're not a service_provider. Try the logging in as a customer",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )


class RefreshToken(APIView):
    serializer_class = TokenRefreshSerializer

    def post(self, request):
        if "refresh" not in request.POST:
            return Response(
                {
                    "code": 400,
                    "status": "Failed",
                    "message": "Refresh token not provided",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            response = Utils.refresh_token(refresh=request.data.get("refresh"))
            if "error" in response.keys():
                return Response(
                    {"code": 401, "status": "Failed", "message": response},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            else:
                return Response(
                    {"code": 200, "status": "Success", "message": response},
                    status=status.HTTP_200_OK,
                )


class PopulateUser(APIView):

    permission_classes = (AllowAny,)

    def get(self, request):

        name = ["JAMES PETER", "JOHN DOE"]
        location = ["Lagos", "Ibadan", "Kano", "Abeokuta", "Benin"]
        role = ["customer", "service_provider"]

        if not (users := User.objects.all()):

            for x in range(1, 11):
                user_name = f"username{x}"
                names = choice(name).split()

                User.objects.create_user(
                    email=f"test{x}@yahoomail.com",
                    password=user_name,
                    username=user_name,
                    first_name=names[0],
                    last_name=names[1],
                    phone_number=f"090{x}-000-000{x}",
                    _is_verified=choice([False, True]),
                    role=choice(role),
                    location=choice(location),
                )
        serialized = UserSerializer(users, many=True)
        return Response(serialized.data)


class PopulateSP(APIView):

    permission_classes = (AllowAny,)

    def get(self, request):
        name = [
            "Electrician",
            "FashionDesigner",
            "WebDeveloper",
            "Marketer",
            "Promoter",
            "Teacher",
        ]
        sp = User.objects.filter(role="service_provider")

        if not User.objects.all():
            for x in range(sp.count()):
                User.objects.create(
                    user=sp[x],
                    business_name=name[x],
                    is_verified_business=choice([False, True]),
                )

        return Response({"message": "SP data populated sucessfully."})


class ChangePassword(APIView):
    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly)

    def get(self, request):
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        data = {}
        old_password = request.data["old_password"]
        password = request.data["password"]
        password2 = request.data["password2"]

        user_id = request.GET.get("user_id")

        obj = User.objects.get(id=user_id)
        self.check_object_permissions(request, obj)

        # serializer = ChangePasswordSerializer(data=data)

        email = request.user.email

        user = authenticate(email=email, password=old_password)

        if user:
            password_validity = Utils.validate_password(password=password)
            if password_validity["status"]:
                if password == password2:
                    user = User.objects.get(email=email)
                    user.set_password(password)
                    user.save()
                    return Response(
                        {"message": "Password changed successfully"},
                        status=status.HTTP_202_ACCEPTED,
                    )
                else:
                    return Response(
                        {"password": "passwords do not match"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            return Response(
                {"password": password_validity["message"]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            return Response(
                {"old password": "Incorrect password"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ResetPasswordEmail(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        email = request.data["email"]
        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)

            relative_link = reverse("reset_password")

            current_site = request.get_host()
            absolute_url = f"{http_protocol}{current_site}{relative_link}"

            email_body = f"""
                        <h2>Hi, <small>{user.first_name}</small></h2>    
                        <h4>Use the link below to verify your email.</h4>
                        <p>{absolute_url}</p>
                        
                        """
            data = {
                "email_subject": "Verify your email",
                "email_body": email_body,
                "to_email": user.email,
            }

            Utils.sending_email(data)

            return Response(
                {
                    "message": "Password Reset email sent",
                    "Reset password link": absolute_url,
                },
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"message": "Invalid user email"}, status=status.HTTP_406_NOT_ACCEPTABLE
            )


class ResetPassword(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        email = request.data["email"]
        password = request.data["password"]
        password2 = request.data["password2"]

        password_validity = Utils.validate_password(password)

        if password_validity["status"]:
            if password2 == password:
                try:
                    user = User.objects.get(email=email)
                    user.set_password(password)
                    user.save()

                    return Response(
                        {"message": "Password reset successful"},
                        status=status.HTTP_200_OK,
                    )
                except Exception as e:
                    return Response({"message": e}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(
                    {"password": "Passwords do not match"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            return Response(
                {"password": password_validity["message"]},
                status=status.HTTP_400_BAD_REQUEST,
            )


class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    client_class = OAuth2Client
