from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [

    # Auth
    path('signup/',  views.signup_view,  name='signup'),
    path('login/',   views.login_view,   name='login'),
    path('logout/',  views.logout_view,  name='logout'),

    # Dashboard
    path('',           views.dashboard, name='dashboard'),
    path('dashboard/', views.dashboard, name='dashboard_alt'),

    # Students
    path('students/',                  views.student_list,   name='student_list'),
    path('students/add/',              views.student_add,    name='student_add'),
    path('students/<int:pk>/',         views.student_detail, name='student_detail'),
    path('students/<int:pk>/edit/',    views.student_edit,   name='student_edit'),
    path('students/<int:pk>/delete/',  views.student_delete, name='student_delete'),

    # Enquiries
    path('enquiries/',                 views.enquiry_list,   name='enquiry_list'),
    path('enquiries/add/',             views.enquiry_add,    name='enquiry_add'),
    path('enquiries/<int:pk>/',        views.enquiry_detail, name='enquiry_detail'),
    path('enquiries/<int:pk>/edit/',   views.enquiry_edit,   name='enquiry_edit'),
    path('enquiries/<int:pk>/delete/', views.enquiry_delete, name='enquiry_delete'),

    # Admissions
    path('admissions/',                  views.admission_list,  name='admission_list'),
    path('admissions/add/',              views.admission_add,   name='admission_add'),
    path('admissions/<int:pk>/',         views.admission_detail,name='admission_detail'),
    path('admissions/<int:pk>/edit/',    views.admission_edit,  name='admission_edit'),
    path('admissions/<int:pk>/delete/',  views.admission_delete,name='admission_delete'),
    path('admissions/<int:pk>/print/',   views.admission_print, name='admission_print'),

    # Fees
    path('fees/',                  views.fees_list,        name='fees_list'),
    path('fees/add/',              views.fees_add,         name='fees_add'),
    path('fees/<int:pk>/',         views.fees_detail,      name='fees_detail'),
    path('fees/<int:pk>/edit/',    views.fees_edit,        name='fees_edit'),
    path('fees/<int:pk>/delete/',  views.fees_delete,      name='fees_delete'),
    path('fees/<int:pk>/receipt/', views.fee_receipt_print,name='fee_receipt'),

    # Courses
    path('courses/',               views.course_list, name='course_list'),
    path('courses/add/',           views.course_add,  name='course_add'),
    path('courses/<int:pk>/edit/', views.course_edit, name='course_edit'),

    # Batches
    path('batches/',               views.batch_list, name='batch_list'),
    path('batches/add/',           views.batch_add,  name='batch_add'),
    path('batches/<int:pk>/edit/', views.batch_edit, name='batch_edit'),

    # Reports
    path('reports/', views.reports, name='reports'),

    # AJAX
    path('ajax/get-student/',    views.get_student_by_id,    name='get_student'),
    path('ajax/get-payments/',   views.get_admission_payments,name='get_payments'),
]