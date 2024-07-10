from django.urls import path
from . import views
from django.urls import include
from django.views.generic import RedirectView

urlpatterns = [
    #path('accounts/', include('django.contrib.auth.urls')),
    #path('', RedirectView.as_view(url='index/', permanent=True)),
    # path('', RedirectView.as_view(url='index', permanent=True)),
    path('accounts/login/', views.handle_login, name = 'login'),
    path('',views.dashboard,name='dashboard'),
    path('user', views.user, name = 'user'),
    path('get_subcategories_for_user/', views.get_subcategories_for_user, name='get_subcategories_for_user'),
    path('get_subcategories_for_officer/', views.get_subcategories_for_officer, name='get_subcategories_for_officer'),
    path('chief', views.chief, name = 'chief'),
    path('validate', views.validate, name = 'validate'), 
    path('officer', views.officer, name = 'officer'), 
    path('general', views.general, name = 'general'), 
    path('upload', views.upload_report, name='upload_report'),
    path('delete_report/<int:report_id>/', views.delete_report, name='delete_report'),
    path('update_report/<int:report_id>/', views.update_report, name='update_report'),
    path('solution/<int:report_id>/', views.solution, name = 'solution'),
    path('solutionForReport/<int:report_id>/', views.solutionForReport, name = 'solutionForReport'),
    path('upload_solution/<int:report_id>/', views.upload_solution, name='upload_solution'),
    path('reports/<str:operation_line>/', views.get_reports_by_status_and_profession, name='get_reports_by_operation_line'),
    path('dashboard', views.dashboard, name= 'dashboard'),
    path('reports_daily/<int:year>/<int:month>/', views.reports_daily, name='reports_daily'),
    path('reports_monthly/<int:year>/', views.reports_monthly, name='reports_monthly'),
    path('reports_today/<int:year>/<int:month>/<int:day>/', views.reports_today, name='reports_today'),
    path('reports_currentMonth/<int:year>/<int:month>/', views.reports_currentMonth, name='reports_currentMonth'),
    path('reports_by_year/<int:year>/', views.reports_by_year, name='reports_by_year'),
    path('reports_by_year_month/<int:year>/<int:month>/', views.reports_by_year_month, name='reports_by_year_month'),
    path('reports_by_year_month_date/<int:year>/<int:month>/<int:day>/', views.reports_by_year_month_date, name='reports_by_year_month_date'),
    path('get_years/', views.get_years, name='get_years'),
    path('error', views.error, name='error'),
    path('success', views.success, name='success'),
    path('export_reports/', views.export_reports, name='export_reports'),

]
