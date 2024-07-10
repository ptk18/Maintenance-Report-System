from django.core.mail import EmailMultiAlternatives
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .decorator import group_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import Report, Profile, Image,Profession, OperationLine, Solution, ImageSolution, SubCategory
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect
import datetime
import os 
import mimetypes
from datetime import date
from datetime import datetime as dateTime
from django.urls import reverse
from django.http import JsonResponse
import uuid
from django.core.files.base import ContentFile

# Create your views here.
def handle_login(request):
    
    if( request.method == 'POST'):
        next_param = request.POST.get('next')
        form = AuthenticationForm(request, data= request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username= username, password= password)
            # print(user)
            if user is not None:
                login(request, user)  # Log the user in
                if user.groups.filter(name='General').exists() and next_param:
                    redirect_url = next_param
                elif user.groups.filter(name='General').exists():
                    redirect_url = '/inform/general'
                elif user.groups.filter(name='User').exists():
                    redirect_url = '/inform/user'
                elif user.groups.filter(name='Chief').exists():
                    redirect_url = '/inform/chief'
                elif user.groups.filter(name='Officer').exists():
                    redirect_url = '/inform/officer'
                elif user.groups.filter(name='Validate').exists():
                    redirect_url = '/inform/validate'
            
                else:
                    messages.error(request, "No group found for the user.")
                    return redirect('/inform/accounts/login/')
                return redirect(redirect_url)
            else:
                messages.error(request, "Invalid username or password.")
                return redirect('/inform/accounts/login/')
        else:
            messages.error(request, "Form is not valid. Please check your username and password.")
            return redirect('/inform/accounts/login/')
    
    '''else:
        if 'next' in request.POST:
            #return redirect(request.POST.get('next'))
            return redirect(request.POST.get('next', '/'))'''

  
    return render(request, 'registration/login.html')

                
@login_required(login_url='/inform/error')
@group_required('User')
def user(request):
    # Assuming reports_per_page is the number of reports you want to show per page
    reports_per_page = 1
    reports = Report.objects.filter(reporterName=request.user.username).order_by('-datetime')
    # For filtering 
    status = request.GET.get('status')

    # For adding status 'complete' to reports
    reportsToComplete = reports.filter(status = '4')
    reportsToComplete = reportsToComplete[:500]
    ReportsToCompletePaginator = Paginator(reportsToComplete, reports_per_page)
    page_number_complete = request.GET.get('pageComplete')
    page_obj_complete = ReportsToCompletePaginator.get_page(page_number_complete)
    
    if status in ['0', '1', '2','3','4','5','6']:  
        reports = reports.filter(status=status)
        reports = reports[:500]
        paginator = Paginator(reports, reports_per_page)
    else: 
        reports = reports[:500]
        paginator = Paginator(reports, reports_per_page)

    # Get all the professions and operations Line number
    professions = Profession.objects.all()
    operation_lines = OperationLine.objects.all()

   
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    
    context = {
        'page_obj': page_obj,
        'professions': professions,
        'operation_lines': operation_lines,
        'status': status,
        'page_obj_complete': page_obj_complete,
    }

    if request.method == 'POST':
        report_id = request.POST.get('report_id')
        report = Report.objects.get(reportID = report_id)
        # Send Mails to General, Chiefs, MD, Officers
        senderName = request.user.username

        # Chief Users
        # First, filter operation line by line number 
        operation_line = OperationLine.objects.get(line_no=report.operationLineNumber)
        # Then, get all profiles that have this operation line
        profiles = Profile.objects.filter(operation_line_no=operation_line)
        # Finally, get chief associated with these profiles
        chiefs = [profile.user for profile in profiles]
        chiefs_emails = [chief.email for chief in chiefs]

        # MD 
        md_group = Group.objects.get(name='Validate')
        md_group_users = User.objects.filter(groups__in=[md_group])
        md_group_users_emails = [user.email for user in md_group_users]

        # General 
        general_group = Group.objects.get(name='General')
        general_group_users = User.objects.filter(groups__in=[general_group])
        general_group_users_emails = [user.email for user in general_group_users]

        # Officers
        officer_group = Group.objects.get(name='Officer')
        # # Get users in the Officer group
        officer_users = User.objects.filter(groups__in=[officer_group])
        # Filter users by profession
        filtered_users = []
        for user in officer_users:
            profile = Profile.objects.get(user=user)
            if profile.profession.filter(profession_name=report.problemCategory).exists():
                filtered_users.append(user)
        officer_mails = [user.email for user in filtered_users]

        if request.POST.get('cancel') == 'Cancel':
            context = {
        'page_obj': page_obj,
        'professions': professions,
        'operation_lines': operation_lines,
        'status': status,
        'page_obj_complete':page_obj_complete
        }
        elif request.POST.get('confirmSolved') == 'confirmSolved' and 'form-submitted' in request.POST:
            report.status = '5'
            report.save()
            send_email_to_user(senderName, report, chiefs_emails, 'Report Solved Confirmed By ')
            send_email_to_user(senderName, report, md_group_users_emails, 'Report Solved Confirmed By ')
            send_email_to_user(senderName, report, officer_mails, 'Report Solved Confirmed By ')
            send_email_to_user(senderName, report, general_group_users_emails, 'Report Solved Confirmed By ')

        elif request.POST.get('notConfirmSolved') == 'notConfirmSolved' 'form-submitted' in request.POST:
            report.status = '6'
            report.rejectedBy = request.user.username
            report.save()
            send_email_to_user(senderName, report, chiefs_emails, 'Report Solved Not Confirmed By ')
            send_email_to_user(senderName, report, md_group_users_emails, 'Report Solved Not Confirmed By ')
            send_email_to_user(senderName, report, officer_mails, 'Report Solved Not Confirmed By ')
            send_email_to_user(senderName, report, general_group_users_emails, 'Report Solved Not Confirmed By ')
        else: 
            context = {
            'page_obj': page_obj,
            'professions': professions,
            'operation_lines': operation_lines,
            'editReport' : report,
            'status': status,
            'page_obj_complete': page_obj_complete,
        }
        # return redirect('user')
    
    # print('context', context)

    return render(request, 'user.html', context)

def get_subcategories_for_user(request):
    problemCategory = request.GET.get('problemCategory')
    if not problemCategory:
        return JsonResponse({'error': 'Nos problemCategory provided'}, status=400)
    
    try:
        profession = Profession.objects.get(profession_name=problemCategory)
        subCategoriesForUser = profession.subCategoryForUser.all().values_list('subCategoryForUser', flat=True)
        return JsonResponse({'subCategoriesForUser': list(subCategoriesForUser)}, safe=False)
    except Profession.DoesNotExist:
        return JsonResponse({'error': 'Profession not found'}, status=404)
    
def get_subcategories_for_officer(request):
    problemCategory = request.GET.get('problemCategory')
    if not problemCategory:
        return JsonResponse({'error': 'Nos problemCategory provided'}, status=400)
    
    try:
        profession = Profession.objects.get(profession_name=problemCategory)
        subCategoriesForOfficer = profession.subCategory.all().values_list('subCategory', flat=True)
        return JsonResponse({'subCategoriesForOfficer': list(subCategoriesForOfficer)}, safe=False)
    except Profession.DoesNotExist:
        return JsonResponse({'error': 'Profession not found'}, status=404)
                            

@login_required(login_url='/inform/error')
@group_required('Chief')
def chief(request):
    user = User.objects.get(username=request.user)
    profile = Profile.objects.get(user=user)
    operation_lines = profile.operation_line_no.all()
    operation_line_nos = [line.line_no for line in operation_lines]
    reports = Report.objects.filter(status='0', operationLineNumber__in= operation_line_nos).order_by('-datetime')  # Filter reports with status = '0'
    reportHistorys = Report.objects.filter(status='0', operationLineNumber__in=operation_line_nos) | \
            Report.objects.filter(status='1', operationLineNumber__in=operation_line_nos) | \
            Report.objects.filter(status='6', operationLineNumber__in=operation_line_nos).order_by('-datetime')
    # This is the filtering process

    # Get all the professions and operations Line number
    professions = Profession.objects.all()
    # Get the filter value from the form
    category = request.GET.get('category', '')
    status = request.GET.get('status')
    print("status", status)
    print("category", category)

    if status in ['0', '1', '6']:
        reportHistorys = reportHistorys.filter(status=status)

    if category:
        # print('here')
        reportHistorys = reportHistorys.filter(problemCategory=category)

    # Pagination
    reports_per_page = 1
    reports= reports[:500]
    paginator = Paginator(reports, reports_per_page)
    reportHistorys = reportHistorys[:500]
    paginatorHistory = Paginator(reportHistorys, reports_per_page)
    page_number = request.GET.get('page')
    page_number_history = request.GET.get('page_history')
    page_obj = paginator.get_page(page_number)
    page_obj_history = paginatorHistory.get_page(page_number_history)
   
    # print("page_obj ",page_obj)
    
    # context = {
    #     'reports': reports,
    # }


    if request.method == 'POST':
        senderName= request.user.username
        if 'confirm' in request.POST:
            report_id = request.POST.get('confirm')
            report = Report.objects.get(reportID = report_id)
            report.status = '1'
            report.confirmedBy = request.user.username
            report.save()
            
            # Sending Mail
            receiver = User.objects.get(username=report.reporterName).email
            md_group = Group.objects.get(name='Validate')
            md_group_users = User.objects.filter(groups__in=[md_group])
            md_group_users_emails = [user.email for user in md_group_users]

            # Send to normal user
            send_email_to_user(senderName, report, [receiver], 'Report Approval')

            # Send to md users
            send_email_to_user(senderName, report, md_group_users_emails, 'Report Approval')

        elif 'cancel' in request.POST:
            report_id = request.POST.get('cancel')
            report = Report.objects.get(reportID = report_id)
            report.status = '6'
            report.rejectedBy = request.user.username
            report.save()
            receiver = User.objects.get(username=report.reporterName).email
           # Send Mail to Normal User
            send_email_to_user(senderName, report, [receiver],'Report Rejection ')

        return redirect('/inform/chief')
    
    context = {
        'page_obj': page_obj,
        'page_obj_history': page_obj_history,
        'professions' : professions,
        'status': status,
        'category': category
    }

    return render(request, 'chief.html', context)

# For md
@login_required(login_url='/inform/error')
@group_required('Validate')
def validate(request):
    reports = Report.objects.filter(status='1').order_by('-datetime')
    reportHistorys = Report.objects.all().order_by('-datetime')

    # Get the filter value from the form
    category = request.GET.get('category', '')
    status = request.GET.get('status')
    # print("status", status)
    # print("category", category)
    if status in ['0', '1', '2', '3', '4', '5', '6']:
        reportHistorys = reportHistorys.filter(status=status)

    if category:
        # print('here')
        reportHistorys = reportHistorys.filter(problemCategory=category)

    # Pagination
    reports_per_page = 1
    reports = reports[:500]
    paginator = Paginator(reports, reports_per_page)
    reportHistorys = reportHistorys[:500]
    paginatorHistory = Paginator(reportHistorys, reports_per_page)
    history_page = request.GET.get('page_history')
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    page_obj_history = paginatorHistory.get_page(history_page)


     # Get all the professions and operations Line number
    professions = Profession.objects.all()

    context = {
        'page_obj': page_obj,
        'page_obj_history': page_obj_history,
        'professions': professions,
        'status': status,
        'category': category
    }
    
    if request.method == 'POST':

        if 'confirm' in request.POST:
            report_id = request.POST.get('confirm')
            report = Report.objects.get(reportID = report_id)
            report.status = '2'
            report.save()

            senderName= request.user.username
            # User
            receiver = User.objects.get(username=report.reporterName).email # Normal user

            # Chief Users
            # First, filter operation line by line number 
            operation_line = OperationLine.objects.get(line_no=report.operationLineNumber)
            # Then, get all profiles that have this operation line
            profiles = Profile.objects.filter(operation_line_no=operation_line)
            # Finally, get chief associated with these profiles
            chiefs = [profile.user for profile in profiles]
            chiefs_emails = [chief.email for chief in chiefs]

            # Officers
            officer_group = Group.objects.get(name='Officer')
            # # Get users in the Officer group
            officer_users = User.objects.filter(groups__in=[officer_group])
            # Filter users by profession
            filtered_users = []
            for user in officer_users:
                profile = Profile.objects.get(user=user)
                if profile.profession.filter(profession_name=report.problemCategory).exists():
                    filtered_users.append(user)
            officer_mails = [user.email for user in filtered_users]

            # Send Mail to Normal User
            send_email_to_user(senderName, report, [receiver],'Report Approved ( GM Level ) ')
            # Send Mail to Chiefs
            send_email_to_user(senderName, report, chiefs_emails,'Report Approved ( GM Level ) ')
            # Send Mail to Officers
            send_email_to_user(senderName, report, officer_mails,'Report Approved ( GM Level ) ')

        elif 'cancel' in request.POST:
            report_id = request.POST.get('cancel')
            report = Report.objects.get(reportID = report_id)
            report.status = '6'
            report.rejectedBy = request.user.username
            report.save()

            senderName= request.user.username
            # User
            receiver = User.objects.get(username=report.reporterName).email # Normal user

            # Chief Users
            # First, filter operation line by line number 
            operation_line = OperationLine.objects.get(line_no=report.operationLineNumber)
            # Then, get all profiles that have this operation line
            profiles = Profile.objects.filter(operation_line_no=operation_line)
            # Finally, get chief associated with these profiles
            chiefs = [profile.user for profile in profiles]
            chiefs_emails = [chief.email for chief in chiefs]

            # Send Mail to Normal User
            send_email_to_user(senderName, report, [receiver],'Report Rejected ( GM Level ) ')
            # Send Mail to Chiefs
            send_email_to_user(senderName, report, chiefs_emails,'Report Rejected ( GM Level ) ')

        return redirect('validate')

    return render(request, 'validate.html', context)

@login_required(login_url='/inform/error')
@group_required('Officer')
def officer(request):

    # for officer profession
    user = User.objects.get(username=request.user)
    profile = Profile.objects.get(user=user)
    professions = profile.profession.all()
    profession = [profession.profession_name for profession in professions]
    subCategories = SubCategory.objects.all()

    # Creating a list of subcategory names
    subCategory_names = [category.subCategory for category in subCategories]
    # print("SubCategories", subCategories)
    # print("Profession", profession)
   
    # For user group General and retriving their emails 
    general_group = Group.objects.get(name='General')
    users_in_general = User.objects.filter(groups=general_group)
    emails = [user.email for user in users_in_general if user.email]

    # For user group CC and retriving their emails 
    cc_group = Group.objects.get(name='CC')
    users_in_cc = User.objects.filter(groups=cc_group)
    ccEmails = [user.email for user in users_in_cc]

    reports = Report.objects.filter(status ='2',problemCategory__in = profession ).order_by('-datetime')
    for report in reports:
        subcategories = report.get_subcategories()
        print(subcategories)

    reportHistorys = Report.objects.filter(status ='2',problemCategory__in = profession ) | \
        Report.objects.filter(status ='3',problemCategory__in = profession ) | \
        Report.objects.filter(status ='4',problemCategory__in = profession ) | \
        Report.objects.filter(status ='5',problemCategory__in = profession ).order_by('-datetime')

    # This is filtering process

    # Get the filter value from the form
    category = request.GET.get('category', '')
    status = request.GET.get('status')
    print("status", status)
    print("category", category)
    if status in ['0', '1', '2', '3', '4', '5', '6']:
        reportHistorys = reportHistorys.filter(status=status)

    if category:
        # print('here')
        reportHistorys = reportHistorys.filter(problemCategory=category)

    # Pagination
    reports_per_page = 1
    reports = reports[:500]
    paginator = Paginator(reports, reports_per_page)
    reportHistorys = reportHistorys[:500]
    paginatorHistory = Paginator(reportHistorys, reports_per_page)
    page_number = request.GET.get('page')
    page_number_history = request.GET.get('page_history')
    page_obj = paginator.get_page(page_number)
    page_obj_history = paginatorHistory.get_page(page_number_history)
    print("page_obj_history ",page_obj_history)
    
    # Get all the professions and operations Line number
    professions = Profession.objects.all()

   

    context = {
        'page_obj': page_obj,
        'emails' : emails,
        'ccEmails': ccEmails,
        'page_obj_history': page_obj_history,
        'professions': professions,
        'status': status,
        'category': category
        # 'subCategories': subCategory_names,
    }

    # For send email
    if request.method == 'POST' and 'form_submitted' in request.POST:
        # print("After sending", request.POST)
        selected_email = request.POST.get('selected_email')
        cc_email = request.POST.get('selected_CCemail')
        subCategory = request.POST.get('selected_subCategory')
        print("Sub Category", subCategory)
        report_ID = request.POST.get('report_id')
        report = Report.objects.get(reportID = report_ID)
        report.status = '3'
        report.sentBy = request.user.username
        report.sentTo = selected_email
        report.subCategory = subCategory
        report.emailNotifyDate = datetime.datetime.now()
        # report.dueDate = datetime.datetime.now() + datetime.timedelta(days=3)
        report.save()

        # link = request.build_absolute_uri(reverse('login'))
        html_content = render_to_string('email.html', {'report': report})
        text_content = strip_tags(html_content)  # Plain text version for email clients that don't support HTML
        subject = "Report Details For General Sent By Officer"
        # message = "Please find the report details below."
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [selected_email,]
        cc_email = [cc_email,]
        # Create email
        email = EmailMultiAlternatives(subject, text_content, email_from, recipient_list,  cc=cc_email if cc_email else None,) 
        email.attach_alternative(html_content, "text/html")

        # Prepare attachments
        attachments = []
        for image in report.images.all():
            # Get the absolute file path for the image
            image_path = os.path.join(settings.MEDIA_ROOT, str(image.imageData))
            if os.path.exists(image_path):
                with open(image_path, 'rb') as f:
                    file_content = f.read()
                    mime_type, _ = mimetypes.guess_type(image_path)
                    attachments.append((image.imageData.name, file_content, mime_type))
            else:
                print(f"Image file not found: {image_path}")

        # Attach files
        for filename, content, mimetype in attachments:
            email.attach(filename, content, mimetype)

        # Send email
        email.send()

        # Report Sent to Users, Chiefs and MD
        senderName = request.user.username
        # Normal user
        receiver = User.objects.get(username=report.reporterName).email 

        # Chief Users
        # First, filter operation line by line number 
        operation_line = OperationLine.objects.get(line_no=report.operationLineNumber)
        # Then, get all profiles that have this operation line
        profiles = Profile.objects.filter(operation_line_no=operation_line)
        # Finally, get chief associated with these profiles
        chiefs = [profile.user for profile in profiles]
        chiefs_emails = [chief.email for chief in chiefs]

        # MD 
        md_group = Group.objects.get(name='Validate')
        md_group_users = User.objects.filter(groups__in=[md_group])
        md_group_users_emails = [user.email for user in md_group_users]

        send_email_to_user(senderName, report, [receiver], 'Issue Sent to General User To Solve',)
        send_email_to_user(senderName, report, chiefs_emails, 'Issue Sent to General User To Solve ',)
        send_email_to_user(senderName, report, md_group_users_emails, 'Issue Sent to General User To Solve ', )

        # Redirect to the same page to avoid form resubmission
        return redirect('officer')

    return render(request, 'officer.html', context)

@login_required(login_url='/inform/error')
@group_required('General')
def general(request):
    # Get the current user's email
    user_email = request.user.email

    # Filter reports with status '4' and sent to the user's email
    reports = Report.objects.filter(
        status='3',
        sentTo=user_email
    ).order_by('-datetime')
    print("reprots", reports)
    # Filter report history with status '4' and sent to the user's email
    # Filter report history with statuses '4', '5', '6', and '7' and sent to the user's email
    reportHistorys = Report.objects.filter(
        status__in=['3', '4', '5', '6'],
        sentTo=user_email
    ).order_by('-datetime')

    # This is the filtering process

    # Get all the professions and operations Line number
    professions = Profession.objects.all()
    # Get the filter value from the form
    category = request.GET.get('category', '')
    status = request.GET.get('status')
    print("status", status)
    print("category", category)

    if status in ['4', '5', '6', '7']:
        reportHistorys = reportHistorys.filter(status=status)

    if category:
        # print('here')
        reportHistorys = reportHistorys.filter(problemCategory=category)

    # Pagination
    reports_per_page = 1
    reports= reports[:500]
    paginator = Paginator(reports, reports_per_page)
    reportHistorys = reportHistorys[:500]
    paginatorHistory = Paginator(reportHistorys, reports_per_page)
    page_number = request.GET.get('page')
    page_number_history = request.GET.get('page_history')
    page_obj = paginator.get_page(page_number)
    page_obj_history = paginatorHistory.get_page(page_number_history)

    
    context = {
        'page_obj': page_obj,
        'page_obj_history': page_obj_history,
        'professions' : professions,
        'status': status,
        'category': category
    }

    return render(request, 'general.html', context)

@login_required(login_url='/inform/error')
@group_required('User')
def upload_report(request):
    if request.method == 'POST':
        reporter_name = request.POST.get('reporterName')
        reporter_nameReal = request.POST.get('reporterNameReal')
        description = request.POST.get('description')
        line_number = request.POST.get('lineNumber')
        problemCategory = request.POST.get('problemCategory')
        machineNumber = request.POST.get('machineNumber')
        subCategoryForOfficer= request.POST.get('subCategoryForOfficer')
        subCategoryForUser= request.POST.get('subCategoryForUser')
        rank= request.POST.get('rank')
        dueDate = request.POST.get('dueDate')
        images = request.FILES.getlist('images')  # Use getlist to get multiple files
        # Fetch the profession that matches the problem category
        profession = get_object_or_404(Profession, profession_name=problemCategory)
        # Check if the profession requires approval
        if profession.no_need_approval:
            status = '2'  # Status for needing approval
        elif profession.no_need_approval_chief:
            status = '1'
        else:
            status = '0'  # Default status, adjust as necessary
        dt_now = datetime.datetime.now().replace(second=0, microsecond=0)
        latest_report = Report.objects.order_by('-reportID').first()
        if latest_report:
            next_reportID = latest_report.reportID + 1
        else:
            next_reportID  = 1

        report = Report(
            reportID=next_reportID,
            reporterName=reporter_name,
            reporterNameReal= reporter_nameReal,
            operationLineNumber=line_number,
            problemDescription=description,
            datetime=dt_now,
            problemCategory=problemCategory,
            subCategoryForUser = subCategoryForUser,
            subCategory = subCategoryForOfficer,
            rank=rank,
            machineNumber=machineNumber,
            status=status,
            dueDate=dueDate,
        )
        report.save()   

        # for image in images:
        #     print(image)
        #     Image.objects.create(report=report, imageData=image)
        for image in images:
            # Generate a random filename using uuid
            ext = image.name.split('.')[-1]  # Get the file extension
            random_filename = f"{uuid.uuid4().hex}.{ext}"
            # Create an image object and set the new filename
            image_obj = Image(report=report, imageData=ContentFile(image.read(), random_filename))
            image_obj.save()
        
        # email sending Chief
        # First, filter operation line by line number
        operation_line = OperationLine.objects.get(line_no=line_number)
        # Then, get all profiles that have this operation line
        profiles = Profile.objects.filter(operation_line_no=operation_line)
        # Finally, get chief associated with these profiles
        chiefs = [profile.user for profile in profiles]
        chiefs_emails = [chief.email for chief in chiefs]

        if status == '1':
            # MD 
            md_group = Group.objects.get(name='Validate')
            md_group_users = User.objects.filter(groups__in=[md_group])
            md_group_users_emails = [user.email for user in md_group_users]
            send_email_to_user(reporter_name, report, md_group_users_emails, 'Issue Reported By User ( No Need Approval Chief) ', )
        elif status == '2':
            # Officers
            officer_group = Group.objects.get(name='Officer')
            # # Get users in the Officer group
            officer_users = User.objects.filter(groups__in=[officer_group])
            # Filter users by profession
            filtered_users = []
            for user in officer_users:
                profile = Profile.objects.get(user=user)
                if profile.profession.filter(profession_name=report.problemCategory).exists():
                    filtered_users.append(user)
            officer_mails = [user.email for user in filtered_users]
             # Send Mail to Officers
            send_email_to_user(reporter_name, report, officer_mails,'Issue Reported ( No need approval Chief and GM) ')
        elif status == '0':
            send_email_to_user(reporter_name, report, chiefs_emails , 'Report Submission')

        return redirect('/inform/user')

    return render(request, 'registration/user.html')

@login_required(login_url='/inform/error')
@group_required('User')
def delete_report(request, report_id):
    if request.POST.get('action') == 'delete':
        report = get_object_or_404(Report, reportID=report_id)
        report.delete()
    return redirect('user')

@login_required(login_url='/inform/error')
@group_required('User')
def update_report(request, report_id):
    
    report = Report.objects.get(reportID = report_id)
    
    if request.method == 'POST':
        description = request.POST.get('description')
        line_number = request.POST.get('lineNumber')
        problemCategory = request.POST.get('problemCategory')
        subCategoryForUsers = request.POST.get('subCategoryForUser')
        rank= request.POST.get('rank')
        machineNumber = request.POST.get('machineNumber')
        images = request.FILES.getlist('images')  # Use getlist to get multiple files
        dueDate = request.POST.get('dueDate')
        dt_now = datetime.datetime.now()

        # Update existing report
        report.operationLineNumber = line_number
        report.problemDescription = description
        report.datetime = dt_now
        report.problemCategory = problemCategory
        report.machineNumber = machineNumber
        report.subCategoryForUser = subCategoryForUsers
        report.rank = rank
        report.dueDate = dueDate
        report.save()
        # Clear existing images associated with the report
        # report.images.all().delete()
        # for image in images:
        #     print(image)
        #     Image.objects.create(report=report, imageData=image)
        for image in images:
            # Generate a random filename using uuid
            ext = image.name.split('.')[-1]  # Get the file extension
            random_filename = f"{uuid.uuid4().hex}.{ext}"
            # Create an image object and set the new filename
            image_obj = Image(report=report, imageData=ContentFile(image.read(), random_filename))
            image_obj.save()

        return redirect('user')
    else:
        return redirect('error')

@login_required(login_url='/inform/error')
@group_required('General')
# After loggin in the user from "General group" can report their solution
def solution(request, report_id):
    report = Report.objects.get(reportID = report_id)
    return render(request, 'solution.html', {'report': report})

# This one is for view the solution for report by the user. 
def solutionForReport(request, report_id):
    report = Report.objects.get(reportID = report_id)
    solution = Solution.objects.get(report = report)
    return render(request, 'solutionForReport.html', {'report': report, 'solution': solution})

#@login_required(login_url='/inform/error')
#@group_required('General')
def upload_solution(request, report_id):
    report = Report.objects.get(reportID = report_id)
    print("report ",report)
    if request.method == 'POST':
        solver_name = request.user.username
        soldescription = request.POST.get('soldescription')
        images = request.FILES.getlist('solimages')

        dt_now = datetime.datetime.now().strftime("%Y-%m-%d")

        latest_solution = Solution.objects.order_by('-solutionID').first()
        if latest_solution:
            next_solutionID = latest_solution.solutionID + 1
        else:
            next_solutionID  = 1

        solution = Solution(
            report=report,
            solutionID=next_solutionID, 
            solverName=solver_name,
            # solutionState=solution_state,
            description=soldescription,
            datetime=dt_now,
        )
        solution.save()

        # for image in images:
        #     ImageSolution.objects.create(solution=solution, imageData=image)
        
        for image in images:
            # Generate a random filename using uuid
            ext = image.name.split('.')[-1]  # Get the file extension
            random_filename = f"{uuid.uuid4().hex}.{ext}"
            # Create an image object and set the new filename
            image_obj = ImageSolution(solution=solution, imageData=ContentFile(image.read(), random_filename))
            image_obj.save()
        # Updating Report Status 

        report.status = '4'
        report.solvedBy = solver_name
        report.finishDate = dt_now

        report.save()



        # Report Email Sent to Users, Chiefs and MD , Officers
        senderName = request.user.username

        # Normal user
        receiver = User.objects.get(username=report.reporterName).email 

        # Chief Users
        # First, filter operation line by line number 
        operation_line = OperationLine.objects.get(line_no=report.operationLineNumber)
        # Then, get all profiles that have this operation line
        profiles = Profile.objects.filter(operation_line_no=operation_line)
        # Finally, get chief associated with these profiles
        chiefs = [profile.user for profile in profiles]
        chiefs_emails = [chief.email for chief in chiefs]

        # MD 
        md_group = Group.objects.get(name='Validate')
        md_group_users = User.objects.filter(groups__in=[md_group])
        md_group_users_emails = [user.email for user in md_group_users]

        # Officers
        officer_group = Group.objects.get(name='Officer')
        # Get users in the Officer group
        officer_users = User.objects.filter(groups__in=[officer_group])
        # Filter users by profession
        filtered_users = []
        for user in officer_users:
            profile = Profile.objects.get(user=user)
            if profile.profession.filter(profession_name=report.problemCategory).exists():
                filtered_users.append(user)
        officer_mails = [user.email for user in filtered_users]

        
        send_email_to_user(senderName, report, [receiver], 'Report Solved By ')
        send_email_to_user(senderName,report,  chiefs_emails, 'Report Solved By ' )
        send_email_to_user(senderName,report, md_group_users_emails, 'Report Solved By ')
        send_email_to_user(senderName,report, officer_mails, 'Report Solved By ')


        return redirect('/inform/success')

    return redirect('/inform/error')


def dashboard(request):
    # Get all the professions and operations Line number
    professions = Profession.objects.all()
    return render( request, 'dashboard.html', {'professions': professions})

'''def get_reports_by_status_and_profession(request, operation_line):
    status = request.GET.get('status')
    profession = request.GET.get('profession')

    if operation_line == 'recent':
        reports = Report.objects.all()
    else:
        reports = Report.objects.filter(operationLineNumber=operation_line)

    if status in ['0', '1', '2', '3', '4','5','6']:
        reports = reports.filter(status=status)

    if profession:
        reports = reports.filter(problemCategory=profession)


    print("reports ",reports)
    # Define the custom order for the status
    status_order = {
        '0': 0,
        '1': 1,  
        '2': 2, 
        '3': 3, 
        '4': 4,  
        '5' : 5,
        '6' : 6,
    }
    # Apply slicing after filtering
    if operation_line == 'recent':
        reports = reports.order_by('-datetime') # Adjust the number of recent reports as needed
        reports = reports.extra(
        select={'status_order': 'FIELD(status, "0", "1", "2", "3", "4","5","6")'}
    ).order_by('status_order')

    #report_list = list(reports.values('reportID', 'reporterName', 'operationLineNumber', 'problemCategory', 'problemDescription', 'status', 'datetime'), reports_images)

    report_list = []
    for report in reports:
        report_images = list(Image.objects.filter(report_id=report.reportID).values('imageData'))
        report_data = {
            'reportID': report.reportID,
            'reporterName': report.reporterName,
            'operationLineNumber': report.operationLineNumber,
            'problemCategory': report.problemCategory,
            'problemDescription': report.problemDescription,
            'status': report.status,
            'datetime': report.datetime,
            'images': report_images,  # Add images to each report
            'dueDate' : report.dueDate,
            'finishDate' : report.finishDate,
        }
        report_list.append(report_data)

    # Add status tags
    status_tags = {
        '0': 'Pending',
        '1': 'Approved',
        '2': 'Validated',
        '3': 'Email Sent',
        '4': 'Solved',
        '5': 'Finished',
        '6': 'Rejected',
    }

    for report in report_list:
        report['status_tag'] = status_tags.get(report['status'], 'Unknown')

    

    return JsonResponse(report_list, safe=False)'''


def get_reports_by_status_and_profession(request, operation_line):
    status = request.GET.get('status')
    profession = request.GET.get('profession')

    if operation_line == 'recent':
        reports = Report.objects.all()
    else:
        reports = Report.objects.filter(operationLineNumber=operation_line)

    if status in ['0', '1', '2', '3', '4', '5', '6']:
        reports = reports.filter(status=status)

    if profession:
        reports = reports.filter(problemCategory=profession)

    # Prefetch report images
    reports = reports.prefetch_related('images')

    # Define the custom order for the status
    status_order = {
        '0': 0,
        '1': 1,
        '2': 2,
        '3': 3,
        '4': 4,
        '5': 5,
        '6': 6,
    }

    # Apply slicing after filtering
    if operation_line == 'recent':
        reports = reports.order_by('-datetime')  # Adjust the number of recent reports as needed
        reports = reports.extra(
            select={'status_order': 'FIELD(status, "0", "1", "2", "3", "4","5","6")'}
        ).order_by('status_order')

    report_list = []
    for report in reports:
        # Fetch the solution and its images
        try:
            solution = Solution.objects.get(report=report)
            solution_images = list(ImageSolution.objects.filter(solution=solution).values('imageData'))
            solution_data = {
                'solutionID': solution.solutionID,
                'solverName': solution.solverName,
                'description': solution.description,
                'datetime': solution.datetime,
                'images': solution_images,
            }
        except Solution.DoesNotExist:
            solution_data = None

        # Fetch report images
        report_images = list(Image.objects.filter(report=report).values('imageData'))

        report_data = {
            'reportID': report.reportID,
            'reporterName': report.reporterName,
            'reporterNameReal': report.reporterNameReal,
            'operationLineNumber': report.operationLineNumber,
            'problemCategory': report.problemCategory,
            'problemDescription': report.problemDescription,
            'subCategory': report.subCategory,
            'subCategoryForUser': report.subCategoryForUser,
            'rank' : report.rank,
            'status': report.status,
            'datetime': report.datetime,
            'dueDate': report.dueDate,
            'finishDate': report.finishDate,
            'images': report_images,  # Add images to each report
            'solution': solution_data,  # Add the solution data
        }

        report_list.append(report_data)

    # Add status tags
    status_tags = {
        '0': 'Pending',
        '1': 'Approved',
        '2': 'Validated',
        '3': 'Email Sent',
        '4': 'Solved',
        '5': 'Finished',
        '6': 'Rejected',
    }

    for report in report_list:
        report['status_tag'] = status_tags.get(report['status'], 'Unknown')

    return JsonResponse(report_list, safe=False)


# For analysis dashboard

# This is for line and bar chart
def reports_daily(request, year, month):
    # Fetch all reports and convert the datetime string to a datetime object
    reports = Report.objects.all()
    report_list = []
    
    for report in reports:
        try:
            report_datetime = datetime.datetime.strptime(report.datetime, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            continue  # Skip if datetime format is incorrect
            
        report_list.append({
            'report': report,
            'datetime': report_datetime,
        })
    
    # Sort the reports by the datetime object in descending order
    sorted_reports = sorted(report_list, key=lambda x: x['datetime'], reverse=True)
    
    # Filter reports based on the chosen year and month, default to current month and year if not specified
    if year and month:
        try:
            year = int(year)
            month = int(month)
        except ValueError:
            year = date.today().year
            month = date.today().month
    else:
        year = date.today().year
        month = date.today().month

    reports_for_month = [item for item in sorted_reports if item['datetime'].year == year and item['datetime'].month == month]
    
    # Group and count reports by day
    data = {}
    for item in reports_for_month:
        day = item['datetime'].date()
        if day not in data:
            data[day] = 0
        data[day] += 1
    
    sorted_data = sorted(data.items())
    sorted_data = [{'day': str(day), 'count': count} for day, count in sorted_data]
    
    return JsonResponse(sorted_data, safe=False)


# This is for line and bar chart
def reports_monthly(request, year=None):
    # Fetch all reports and convert the datetime string to a datetime object
    reports = Report.objects.all()
    report_list = []
    
    for report in reports:
        try:
            report_datetime = datetime.datetime.strptime(report.datetime, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            continue  # Skip if datetime format is incorrect
            
        report_list.append({
            'report': report,
            'datetime': report_datetime,
        })
    
    # Sort the reports by the datetime object in descending order
    sorted_reports = sorted(report_list, key=lambda x: x['datetime'], reverse=True)
    
    # Filter reports for the chosen year or default to current year
    if year:
        try:
            year = int(year)
        except ValueError:
            year = date.today().year
    else:
        year = date.today().year
        
    reports_for_year = [item for item in sorted_reports if item['datetime'].year == year]
    
    # Group and count reports by month
    data = {}
    for item in reports_for_year:
        month = (item['datetime'].year, item['datetime'].month)
        if month not in data:
            data[month] = 0
        data[month] += 1
    
    sorted_data = sorted(data.items())
    sorted_data = [{'month': f'{year}-{month:02}', 'count': count} for (year, month), count in sorted_data]
    
    return JsonResponse(sorted_data, safe=False)


def reports_currentMonth(request, year, month):
    # Get current date
    current_date = date.today()
    
    # Fetch all reports (assuming datetime is a char field)
    reports = Report.objects.all()
    
    # Determine the target year and month based on input parameters
    if year and month:
        try:
            year = int(year)
            month = int(month)
        except ValueError:
            return JsonResponse({'error': 'Invalid year or month format'}, status=400)
    elif year:
        try:
            year = int(year)
            month = 1  # Default to January if only year is specified
        except ValueError:
            return JsonResponse({'error': 'Invalid year format'}, status=400)
    else:
        year = current_date.year
        month = current_date.month
    # Filter reports for the specified month and year
    reports_filtered = [
        report for report in reports
        if report.datetime.startswith(f"{year}-{month:02}")
    ]
    
    # Group and count reports by problem category
    categories_data = {}
    for report in reports_filtered:
        if report.problemCategory in categories_data:
            categories_data[report.problemCategory] += 1
        else:
            categories_data[report.problemCategory] = 1
    
    # Convert categories_data into the format required by Chart.js
    categories_labels = list(categories_data.keys())
    categories_counts = list(categories_data.values())
    
    # Group and count reports by status
    statuses_data = {}
    for report in reports_filtered:
        if report.status in statuses_data:
            statuses_data[report.status] += 1
        else:
            statuses_data[report.status] = 1
    
    # Convert statuses_data into the format required by Chart.js
    statuses_labels = list(statuses_data.keys())
    statuses_counts = list(statuses_data.values())
    
    data = {
        'categories_labels': categories_labels,
        'categories_counts': categories_counts,
        'statuses_labels': statuses_labels,
        'statuses_counts': statuses_counts,
    }
    
    return JsonResponse(data)


def reports_today(request, year=None, month=None, day=None):
    # Get current date
    current_date = date.today()
    
    # Fetch all reports (assuming datetime is a char field)
    reports = Report.objects.all()

    # Determine the target date based on input parameters
    if year and month and day:
        try:
            target_date = datetime.datetime.strptime(f'{year}-{month}-{day}', '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'error': 'Invalid year, month, or day format'}, status=400)
    elif year and month:
        try:
            target_date = datetime.datetime.strptime(f'{year}-{month}-01', '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'error': 'Invalid year or month format'}, status=400)
    else:
        target_date = current_date

    # Filter reports for the target date
    reports_filtered = [report for report in reports if report.datetime.startswith(str(target_date))]

    # Group and count reports by problem category
    categories_data = {}
    for report in reports_filtered:
        if report.problemCategory in categories_data:
            categories_data[report.problemCategory] += 1
        else:
            categories_data[report.problemCategory] = 1
    
    # Convert categories_data into the format required by Chart.js
    categories_labels = list(categories_data.keys())
    categories_counts = list(categories_data.values())
    
    # Group and count reports by status
    statuses_data = {}
    for report in reports_filtered:
        if report.status in statuses_data:
            statuses_data[report.status] += 1
        else:
            statuses_data[report.status] = 1
    
    # Convert statuses_data into the format required by Chart.js
    statuses_labels = list(statuses_data.keys())
    statuses_counts = list(statuses_data.values())
    
    data = {
        'categories_labels': categories_labels,
        'categories_counts': categories_counts,
        'statuses_labels': statuses_labels,
        'statuses_counts': statuses_counts,
    }
    
    return JsonResponse(data)


# for display years for selection
def get_years(request):
    reports = Report.objects.all()
    years = set()
    
    for report in reports:
        try:
            report_date = datetime.datetime.strptime(report.datetime, '%Y-%m-%d %H:%M:%S')
            years.add(report_date.year)
        except ValueError:
            continue
    
    sorted_years = sorted(years, reverse=True)
    return JsonResponse({'years': sorted_years})


# for displaying report counts
def reports_by_year(request, year):
    reports = Report.objects.filter(datetime__startswith=str(year))
    total_reports = reports.count()
    return JsonResponse({'year': year, 'total_reports': total_reports})

def reports_by_year_month(request, year, month):
    month_str = f"{month:02d}"  # Ensure month is two digits
    date_prefix = f"{year}-{month_str}"
    reports = Report.objects.filter(datetime__startswith=date_prefix)
    total_reports = reports.count()
    return JsonResponse({'year': year, 'month': month, 'total_reports': total_reports})

def reports_by_year_month_date(request, year, month, day):
    month_str = f"{month:02d}"  # Ensure month is two digits
    day_str = f"{day:02d}"      # Ensure day is two digits
    date_prefix = f"{year}-{month_str}-{day_str}"
    reports = Report.objects.filter(datetime__startswith=date_prefix)
    total_reports = reports.count()
    return JsonResponse({'year': year, 'month': month, 'day': day, 'total_reports': total_reports})


def error(request):
    return render(request, 'error.html')

def success(request):
    return render(request, 'success.html')


from django.core.mail import send_mail

def send_email_to_user(sender_name, report, selected_emails , subject):
    
    html_content = render_to_string('emailForUsers.html', {'report': report})
    text_content = strip_tags(html_content)  # Plain text version for email clients that don't support HTML
    subject += f' : By {sender_name}'
    # message = "Please find the report details below."
    email_from = settings.EMAIL_HOST_USER
    recipient_list = selected_emails # [selected_email1, selected_email2, ...]

    # Create email
    email = EmailMultiAlternatives(subject, text_content, email_from, recipient_list,) 
    email.attach_alternative(html_content, "text/html")

    # Prepare attachments
    attachments = []
    for image in report.images.all():
        # Get the absolute file path for the image
        image_path = os.path.join(settings.MEDIA_ROOT, str(image.imageData))
        if os.path.exists(image_path):
            with open(image_path, 'rb') as f:
                file_content = f.read()
                mime_type, _ = mimetypes.guess_type(image_path)
                attachments.append((image.imageData.name, file_content, mime_type))
        else:
            print(f"Image file not found: {image_path}")

    # Attach files
    for filename, content, mimetype in attachments:
        email.attach(filename, content, mimetype)

    # Send email
    email.send()



from django.http import HttpResponse
from .models import Report, Profession
from django.db.models import Q
import openpyxl

def export_reports(request):

    STATUS_MAP = {
            '0': 'Pending',
            '1': 'Approved',
            '2': 'Validated',
            '3': 'Email Sent',
            '4': 'Solved',
            '5': 'Finished',
            '6': 'Rejected',
    }
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        categories = request.POST.get('category')


        filters = Q()
        if start_date and end_date:
            filters &= Q(datetime__range=[start_date, end_date])

        reports = Report.objects.filter(filters).order_by('-datetime')

        print(categories)
        # Apply category filter if specified
        if categories:
            reports = reports.filter(problemCategory=categories)

        # Create the Excel workbook and worksheet
        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        worksheet.title = 'Filtered Reports'

        # Define headers
        headers = ['Report ID', 'Reporter Name', 'Machine Number', 'Operation Line', 'Problem Main Category',  'SubCategory1', 'SubCategory2','Rank', 'Status', 'Problem Description', 'Due Date', 'Finish Date', 'Created Date', 'Confirmed By', 'Sent By', 'Sent To', 'Solved By', 'Rejected By' ]
        worksheet.append(headers)

        # Add data rows
        for report in reports:
            row = [
                report.reportID,
                report.reporterName,
                report.machineNumber,
                report.operationLineNumber,
                report.problemCategory,
                report.subCategory,
                report.subCategoryForUser,
                report.rank,
                STATUS_MAP.get(report.status),
                report.problemDescription,
                report.dueDate,
                report.finishDate if report.finishDate else '',
                report.datetime if report.datetime else '',
                report.confirmedBy if report.confirmedBy else '',
                report.sentBy if report.sentBy else '',
                report.sentTo if report.sentTo else '',
                report.solvedBy if report.solvedBy else '',
                report.rejectedBy if report.rejectedBy else ''

            ]
            worksheet.append(row)

        # Prepare response for Excel download
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="filtered_reports.xlsx"'
        workbook.save(response)
        
        return response

    # If GET request, render the form
    professions = Profession.objects.all()
    return render(request, 'export.html', {'professions': professions})