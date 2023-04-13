from django.shortcuts import render,redirect
from django.views import View
import json
from django.http import JsonResponse
from django.contrib.auth.models import User
from validate_email import validate_email
from django.contrib import messages
from django.core.mail import EmailMessage
from django.core.mail import send_mail
from django.contrib import auth

from django.urls import reverse
from django.utils.encoding import  force_bytes, force_str, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.sites.shortcuts import get_current_site
from .utils import token_generator
from django.contrib.auth.tokens import PasswordResetTokenGenerator



# Create your views here.


class UsernameValidationView(View):
    def post(self,request):
        data = json.loads(request.body)
        username = data['username']
        if not str(username).isalnum():
            return JsonResponse({'username_error':'username should only contain alphanumeric and numbers'},status=400)
        
        if User.objects.filter(username=username).exists():
            return JsonResponse({'username_error':'sorry this username is already taken please choose any other username'},status=409)
        
        
        return JsonResponse({'username_valid':True})
    
class EmailValidationView(View):
    def post(self,request):
        data = json.loads(request.body)
        email = data['email']
        
        if not validate_email(email) :
            return JsonResponse({'email_error':'email is not valid'},status=400)
        
        
        if User.objects.filter(email=email).exists():
            return JsonResponse({'email_error':'sorry this email is already taken please choose any other email'},status=409)
        
        
        return JsonResponse({'email_valid':True})
    
class RegistrationView(View):
    def get(self,request):
        return render(request,'authentication/register.html')
    
    def post(self,request):
        
        #Get data
        #create user
        #validate
        
    
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        
        context = {
            'fieldValues': request.POST
        }
        
        if not User.objects.filter(username=username).exists():
            if not User.objects.filter(email=email).exists():
                
                if len(password) < 8 :
                    messages.error(request,"Password is too short")
                    return render(request,'authentication/register.html',context)
                
                user = User.objects.create_user(username=username,email=email)
                user.set_password(password)
                user.is_active = False
                user.save()
                
                ## domain we are on
                ## relative url
                ## encode uid
                ## token
                
                current_site = get_current_site(request)
                email_body = {
                    'user': user,
                    'domain': current_site.domain,
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': token_generator.make_token(user),
                }

                link = reverse('activate', kwargs={
                               'uidb64': email_body['uid'], 'token': email_body['token']})

                email_subject = 'Activate your account'

                activate_url = 'http://'+current_site.domain+link
            
                email = send_mail(
                    email_subject,
                    'Hi '+user.username + ', Please click the link below to activate your account \n'+activate_url,
                    'noreply@verification.com',
                    [email],
                    fail_silently=True,
                    
                    
                )
                #email.send(fail_silently=False)
                messages.success(request, 'Account successfully created')
       
        return render(request,'authentication/register.html')

class VerificationView(View):
    def get(self, request, uidb64, token):

        try:
            id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=id)

            if not token_generator.check_token(user, token):
                return redirect('login' + "?message" + user.username +"already activated")

            if user.is_active:
                return redirect('login')

            user.is_active = True
            user.save()
            messages.success(request,"Account activated Successfully")
            return redirect('login')

        except Exception as e:
            pass
        return redirect('login')


class LoginView(View):
    def get(self, request):
        return render(request, 'authentication/login.html')

    def post(self, request):
        username = request.POST['username']
        password = request.POST['password']

        if username and password:
            user = auth.authenticate(username=username, password=password)

            if user:
                if user.is_active:
                    auth.login(request, user)
                    messages.success(request,"Welcome " + user.username + " You are are now logged in")
                    return redirect('expense')
                messages.error(request,"Account is not activated.Please activate your account.")
                return render(request, 'authentication/login.html')

            messages.error(request, "Invalid username and password. Please try again")
            return render(request, 'authentication/login.html')
        messages.error(request, "Please fill all the fields")
        return render(request, 'authentication/login.html')

class LogoutView(View):
    def post(self, request):
        auth.logout(request)
        messages.success(request,'You have been logged out')
        return redirect('login')

class RequestPasswordView(View):
    def get(self, request):
        return render(request, 'authentication/reset_password.html')

    def post(self, request):


        email = request.POST['email']
        context = {
            'values': request.POST
        }

        if not validate_email(email):
            messages.error(request,"Please provide a valid email!")
            return render(request,'authentication/reset_password.html', context)

        current_site = get_current_site(request)
        user = User.objects.filter(email=email)
        if user.exists():

            email_contents = {
                'user': user[0],
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user[0].pk)),
                'token': PasswordResetTokenGenerator().make_token(user[0]),
            }

            link = reverse('reset-password', kwargs={
                'uidb64': email_contents['uid'], 'token': email_contents['token']})

            email_subject = 'Reset your password'

            reset_url = 'http://' + current_site.domain + link

            email = send_mail(
                email_subject,
                'Hi there,  Please click the link below to create new password for your account \n' + reset_url,
                'noreply@verification.com',
                [email],
                fail_silently=True,

            )
        messages.success(request,"We have send you the email to reset the password")
        return render(request, 'authentication/reset_password.html', context)

class PasswordResetView(View):
    def get(self,request, uidb64, token):
        context = {
            'uidb64' : uidb64,
            'token' : token
        }
        try:
            user_id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=user_id)
            if not PasswordResetTokenGenerator().check_token(user, token):
                messages.info(request, "The link is invalid, Please request a new link")
                return render(request, 'authentication/reset_password.html', context)
            return redirect('login')

        except Exception as e:
            messages.info(request, "Something went wrong")
            return render(request, 'authentication/new_password.html', context)


    def post(self,request, uidb64, token):

        context = {
            'uidb64': uidb64,
            'token': token

        }

        password = request.POST['password']
        password2 = request.POST['confirmpassword']

        if password != password2:
            messages.error(request, "Passwords do not match")
            return render(request, 'authentication/new_password.html', context)
        if len(password) < 8:
            messages.error(request, "Password is too short")
            return render(request, 'authentication/new_password.html', context)

        try:
            user_id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=user_id)
            user.set_password(password)
            user.save()
            messages.success(request, "Password reset Successfully. You can now login with new password")
            return redirect('login')

        except Exception as e:
            messages.info(request, "Something went wrong")
            return render(request, 'authentication/new_password.html', context)





