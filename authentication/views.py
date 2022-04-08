from rest_framework import status
from rest_framework.response import Response
from .serializers import CustomerRegistrationSerializer, SPRegistrationSerializer
from .models import User, ServiceProvider
from rest_framework_simplejwt.tokens import RefreshToken
from src.utils import Utils, otp_session
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.conf import settings
from django.shortcuts import get_list_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from .permissions import PostReadAllPermission
from django.core.exceptions import ObjectDoesNotExist
import jwt

from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView




class CustomerRegisterGetAll(APIView):
    # permission_classes = (PostReadAllPermission,)
    queryset = User.objects.all()
    serializer_class = CustomerRegistrationSerializer

    def get(self, request):
        users_objs = get_list_or_404(User, role="customer")
        users_serilizer = CustomerRegistrationSerializer(users_objs, many=True)
        data = {
            "message": "Successfully retrieved customers",
            "data": users_serilizer.data,
        }
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = CustomerRegistrationSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()

            user_data = serializer.data

            user = User.objects.get(email=user_data["email"])

            token = RefreshToken.for_user(user).access_token

            relative_link = reverse("verify_email")

            current_site = get_current_site(request).domain

            absolute_url = f"http://{current_site}{relative_link}?token={str(token)}"

            email_body = f"Hi, {user.first_name},\n    Use the link below to verify your email.\n              {absolute_url}"

            data = {
                "email_subject": "Verify your email",
                "email_body": email_body,
                "to_email": user.email,
            }

            Utils.send_email(data)

            return_data = dict(serializer.data)
            return_data["verification_link"] = absolute_url

            return Response(return_data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Not in use yet. Still needs to be fixed.
class CustomerRetrieveUpdateDelete(APIView):
    queryset = User.objects.all()
    serializer_class = CustomerRegistrationSerializer
    permission_classes = (IsAuthenticated,)

    def get(self, id, request):

        customer = User.objects.get(id=id)
        serializer = CustomerRegistrationSerializer(customer)
        if customer:
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_404_NOT_FOUND)

    def put(self, id, request):
        customer = User.objects.get(id=id)
        if customer:
            serializer = CustomerRegistrationSerializer(
                customer, data=request.data)
            if serializer.is_valid():
                serializer.save()

                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(
                {"message": "Invalid User ID", "status": status.HTTP_404_NOT_FOUND}
            )

    def delete(self, id, request):
        customer = User.objects.get(id=id)
        if customer:
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
    queryset = ServiceProvider.objects.all()
    serializer_class = SPRegistrationSerializer
    permission_classes = (PostReadAllPermission,)

    def get(self, request):
        users_objs = get_list_or_404(User, role="service_provider")
        users_serilizer = CustomerRegistrationSerializer(users_objs, many=True)
        data = {
            "message": "Successfully retrieved customers",
            "data": users_serilizer.data,
        }
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = SPRegistrationSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            user_data = serializer.data

            user = User.objects.get(email=user_data["email"])

            token = RefreshToken.for_user(user).access_token

            relative_link = reverse("verify_email")

            current_site = get_current_site(request).domain

            absolute_url = f"http://{current_site}{relative_link}?token={str(token)}"

            email_body = f"Hi, {user.first_name},\n    Use the link below to verify your email.\n              {absolute_url}"

            data = {
                "email_subject": "Verify your email",
                "email_body": email_body,
                "to_email": user.email,
            }

            Utils.send_email(data)

            return_data = dict(serializer.data)
            return_data["verification_link"] = absolute_url

            return Response(return_data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Not in use yet. Still needs to be fixed.
class ServiceProviderRetrieveUpdateDelete(APIView):
    queryset = ServiceProvider.objects.all()
    serializer_class = SPRegistrationSerializer

    def get(self, id, request):

        service_provider = ServiceProvider.objects.get(id=id)
        serializer = SPRegistrationSerializer(service_provider)
        if service_provider:
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_404_NOT_FOUND)

    def put(self, id, request):
        service_provider = ServiceProvider.objects.get(id=id)
        if service_provider:
            serializer = SPRegistrationSerializer(
                service_provider, data=request.data)
            if serializer.is_valid():
                serializer.save()

                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(
                {"message": "Invalid User ID", "status": status.HTTP_404_NOT_FOUND}
            )

    def delete(self, id, request):
        try:
            service_provider = ServiceProvider.objects.get(id=id)
            service_provider.delete()
            return Response(
                {
                    "message": "User deleted successfully",
                    "status": status.HTTP_204_NO_CONTENT,
                }
            )
        except ObjectDoesNotExist:
            return Response(
                {"message": "Invalid User ID", "status": status.HTTP_404_NOT_FOUND}
            )


class VerifyEmail(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        token = request.GET.get("token")
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=["HS256"])
            user = User.objects.get(id=payload["user_id"])

            if not user.is_verified:
                user.is_verified = True
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

    permission_classes = (IsAuthenticated,)

    def post(self, request):

        otp_code = request.data.get('otp')
        user = User.objects.get(id=request.user.id)

        serializer = CustomerRegistrationSerializer(user, many=False)
        phone_number = serializer.data['phone_number']

        try:
            if not user.phone_verification:
                if not 'code' in request.session.keys():
                    sent_otp = otp_session(request, phone_number)
                    if sent_otp:
                        return Response({
                            'status': status.HTTP_200_OK,
                            'message': 'OTP sent successfully'
                        }
                        )
                    return Response({
                        'status': status.HTTP_400_BAD_REQUEST,
                        "message": 'Sending OTP Error'
                    }
                    )
                else:
                    if otp_code:
                        if str(otp_code) == str(request.session['code']):
                            user.phone_verification = True
                            user.save()

                            request.session.clear()
                            return Response({
                                'status': status.HTTP_200_OK,
                                'message': 'OTP Code Verified'
                            }
                            )
                        request.session.clear()
                        return Response({
                            'status': status.HTTP_400_BAD_REQUEST,
                            'message': 'OTP Incorrect!'
                        }
                        )
                    request.session.clear()
                    return Response({
                        'status': status.HTTP_400_BAD_REQUEST,
                        'message': 'Invalid OTP!'
                    }
                    )
            return Response({
                'status': status.HTTP_403_FORBIDDEN,
                'message': 'Phone number already validated'
            }
            )
        except jwt.ExpiredSignatureError:
            return Response({
                'status': status.HTTP_400_BAD_REQUEST,
                "message": "Verification link expired"
            }
            )
        except jwt.exceptions.DecodeError:
            return Response({
                'status': status.HTTP_400_BAD_REQUEST,
                "message": "Invalid token",
            }
            )


class UpdatePhone(APIView):

    permission_classes = (IsAuthenticated, )

    def post(self, request):

        otp_code, new_number = request.data.get(
            'otp'), request.data.get('number')
        user = User.objects.get(id=request.user.id)  
        print(user.is_verified)
        try:
            if not User.objects.filter(
                    phone_number__iexact=new_number).exists():

                if not 'code' in request.session.keys():
                    sent_otp = otp_session(request, new_number)
                    if sent_otp:
                        return Response({
                            'status': status.HTTP_200_OK,
                            'message': 'OTP sent successfully'
                        }
                        )
                    return Response({
                        'status': status.HTTP_400_BAD_REQUEST,
                        "message": 'Sending OTP Error'
                    }
                    )

                else:
                    if otp_code:
                        if str(otp_code) == str(request.session['code']):
                            user.phone_verification = True
                            user.phone_number = new_number
                            user.save()

                            request.session.clear()
                            return Response({
                                'status': status.HTTP_200_OK,
                                'message': 'OTP Code Verified'
                            }
                            )
                        request.session.clear()
                        return Response({
                            'status': status.HTTP_400_BAD_REQUEST,
                            'message': 'OTP Incorrect!'
                        }
                        )
                    request.session.clear()
                    return Response({
                        'status': status.HTTP_400_BAD_REQUEST,
                        'message': 'Invalid OTP!'
                    }
                    )
            
            return Response({
                    'status': status.HTTP_403_FORBIDDEN,
                    'message': 'Phone number already Exist'
                }
                )
        
        except jwt.ExpiredSignatureError:
            return Response({
                'status': status.HTTP_400_BAD_REQUEST,
                "message": "Verification link expired"
            }
            )
        except jwt.exceptions.DecodeError:
            return Response({
                'status': status.HTTP_400_BAD_REQUEST,
                "message": "Invalid token",
            }
            )


class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    client_class = OAuth2Client
