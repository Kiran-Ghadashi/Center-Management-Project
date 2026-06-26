from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncMonth
from django.http import JsonResponse
from django.utils import timezone
from .models import Student, Enquiry, Admission, Fees, Course, Batch
from .forms import (StudentForm, EnquiryForm, AdmissionForm,
                    FeesForm, CourseForm, BatchForm, SignupForm)


# ═══════════════════════════════════════════════
# AUTH
# ═══════════════════════════════════════════════
def signup_view(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    form = SignupForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, f'Welcome {user.username}!')
        return redirect('core:dashboard')
    return render(request, 'core/signup.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    form = AuthenticationForm(data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        messages.success(request, f'Welcome back, {form.get_user().username}!')
        return redirect('core:dashboard')
    return render(request, 'core/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('core:login')


# ═══════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════
@login_required
def dashboard(request):
    today         = timezone.now().date()

    # month/year filter from GET params — default to current month
    month = int(request.GET.get('month', today.month))
    year  = int(request.GET.get('year',  today.year))

    # summary cards — all time
    total_enquiries      = Enquiry.objects.count()
    total_admissions     = Admission.objects.count()
    pending_enquiries    = Enquiry.objects.filter(status='pending').count()
    followup_enquiries   = Enquiry.objects.filter(status='followup').count()
    total_fees_collected = Fees.objects.aggregate(t=Sum('amount_paid'))['t'] or 0
    total_fees_pending   = sum(a.fees_pending for a in Admission.objects.all())

    # filtered by selected month/year
    admissions_this_month = Admission.objects.filter(
        admission_date__month=month, admission_date__year=year
    ).count()
    fees_this_month = Fees.objects.filter(
        payment_date__month=month, payment_date__year=year
    ).aggregate(t=Sum('amount_paid'))['t'] or 0
    enquiries_this_month = Enquiry.objects.filter(
        enquiry_date__month=month, enquiry_date__year=year
    ).count()

    # recent 5 records
    recent_enquiries  = Enquiry.objects.order_by('-enquiry_date')[:5]
    recent_admissions = Admission.objects.select_related(
        'student', 'course'
    ).order_by('-admission_date')[:5]
    recent_fees       = Fees.objects.select_related(
        'admission__student'
    ).order_by('-payment_date')[:5]

    # month/year options for filter dropdown (last 12 months)
    import calendar
    month_choices = []
    for i in range(11, -1, -1):
        d = today.replace(day=1)
        from datetime import timedelta
        d = d - timedelta(days=30 * i)
        month_choices.append({
            'month': d.month,
            'year' : d.year,
            'label': d.strftime('%B %Y')
        })

    context = {
        'total_enquiries'      : total_enquiries,
        'total_admissions'     : total_admissions,
        'pending_enquiries'    : pending_enquiries,
        'followup_enquiries'   : followup_enquiries,
        'total_fees_collected' : total_fees_collected,
        'total_fees_pending'   : total_fees_pending,
        'admissions_this_month': admissions_this_month,
        'fees_this_month'      : fees_this_month,
        'enquiries_this_month' : enquiries_this_month,
        'recent_enquiries'     : recent_enquiries,
        'recent_admissions'    : recent_admissions,
        'recent_fees'          : recent_fees,
        'month_choices'        : month_choices,
        'selected_month'       : month,
        'selected_year'        : year,
        'selected_label'       : f'{today.strftime("%B")} {year}',
    }
    return render(request, 'core/dashboard.html', context)


# ═══════════════════════════════════════════════
# STUDENT VIEWS
# ═══════════════════════════════════════════════
@login_required
def student_list(request):
    students = Student.objects.all()
    search   = request.GET.get('search', '')
    if search:
        students = students.filter(
            Q(student_id__icontains=search) |
            Q(full_name__icontains=search)  |
            Q(phone__icontains=search)
        )
    return render(request, 'core/student_list.html', {
        'students': students, 'search': search
    })


@login_required
def student_add(request):
    form = StudentForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Student added successfully.")
        return redirect('core:admission_add')
    return render(request, 'core/student_form.html', {
        'form': form, 'title': 'Add New Student', 'btn': 'Save Student'
    })

@login_required
def student_list(request):
    students = Student.objects.all()
    return render(request, 'core/student_list.html', {'students': students})

@login_required
def student_detail(request, pk):
    obj = get_object_or_404(Student, pk=pk)
    return render(request, 'core/student_detail.html', {'student': obj})

@login_required
def student_edit(request, pk):
    obj  = get_object_or_404(Student, pk=pk)
    form = StudentForm(request.POST or None, request.FILES or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f"Student '{obj.full_name}' updated.")
        return redirect('core:student_list')
    return render(request, 'core/student_form.html', {
        'form': form, 'title': f'Edit Student — {obj.full_name}', 'btn': 'Update Student'
    })

@login_required
def student_delete(request, pk):
    obj = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, f"Student '{obj.full_name}' deleted.")
        return redirect('core:student_list')
    return render(request, 'core/confirm_delete.html', {
        'object': obj, 'object_name': obj.full_name, 'cancel_url': 'core:student_list'
    })


# AJAX — fetch student data by student_id for auto-fill
@login_required
def get_student_by_id(request):
    student_id = request.GET.get('student_id', '').strip()
    try:
        s = Student.objects.get(student_id=student_id)
        return JsonResponse({
            'found'    : True,
            'pk'       : s.pk,
            'full_name': s.full_name,
            'phone'    : s.phone,
            'email'    : s.email,
            'gender'   : s.gender,
        })
    except Student.DoesNotExist:
        return JsonResponse({'found': False})


# ═══════════════════════════════════════════════
# ENQUIRY VIEWS
# ═══════════════════════════════════════════════
@login_required
def enquiry_list(request):
    enquiries = Enquiry.objects.select_related('student').all()
    search    = request.GET.get('search', '')
    status    = request.GET.get('status', '')
    reference = request.GET.get('reference', '')
    if search:
        enquiries = enquiries.filter(
            Q(student_name__icontains=search) |
            Q(phone__icontains=search)        |
            Q(course_interested__icontains=search) |
            Q(student__student_id__icontains=search)
        )
    if status:
        enquiries = enquiries.filter(status=status)
    if reference:
        enquiries = enquiries.filter(reference=reference)
    return render(request, 'core/enquiry_list.html', {
        'enquiries'         : enquiries,
        'search'            : search,
        'selected_status'   : status,
        'selected_reference': reference,
        'status_choices'    : Enquiry.STATUS_CHOICES,
        'reference_choices' : Enquiry.REFERENCE_CHOICES,
        'total_count'       : enquiries.count(),
    })


@login_required
def enquiry_add(request):
    form = EnquiryForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        obj          = form.save(commit=False)
        obj.added_by = request.user
        # if student was selected, auto-fill name/phone from student record
        if obj.student:
            obj.student_name = obj.student.full_name
            obj.phone        = obj.student.phone
            obj.email        = obj.student.email
        obj.save()
        messages.success(request, f'Enquiry for {obj.student_name} added.')
        return redirect('core:enquiry_list')
    return render(request, 'core/enquiry_form.html', {
        'form': form, 'title': 'Add Enquiry', 'btn': 'Save Enquiry'
    })


@login_required
def enquiry_edit(request, pk):
    obj  = get_object_or_404(Enquiry, pk=pk)
    form = EnquiryForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Enquiry updated.')
        return redirect('core:enquiry_list')
    return render(request, 'core/enquiry_form.html', {
        'form': form, 'title': 'Edit Enquiry', 'btn': 'Update Enquiry'
    })


@login_required
def enquiry_delete(request, pk):
    obj = get_object_or_404(Enquiry, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Enquiry deleted.')
        return redirect('core:enquiry_list')
    return render(request, 'core/confirm_delete.html', {
        'object_name': obj.student_name, 'cancel_url': 'core:enquiry_list'
    })


@login_required
def enquiry_detail(request, pk):
    return render(request, 'core/enquiry_detail.html', {
        'enquiry': get_object_or_404(Enquiry, pk=pk)
    })


# ═══════════════════════════════════════════════
# ADMISSION VIEWS
# ═══════════════════════════════════════════════
@login_required
def admission_list(request):
    admissions = Admission.objects.select_related(
        'student', 'course', 'batch'
    ).all()
    search = request.GET.get('search', '')
    course = request.GET.get('course', '')
    batch  = request.GET.get('batch', '')
    if search:
        admissions = admissions.filter(
            Q(student__full_name__icontains=search) |
            Q(student__student_id__icontains=search)|
            Q(student__phone__icontains=search)     |
            Q(course__name__icontains=search)
        )
    if course:
        admissions = admissions.filter(course__id=course)
    if batch:
        admissions = admissions.filter(batch__id=batch)

    admission_data = [{
        'obj'          : a,
        'fees_paid'    : a.fees_paid,
        'fees_pending' : a.fees_pending,
        'is_fully_paid': a.is_fully_paid,
    } for a in admissions]

    return render(request, 'core/admission_list.html', {
        'admission_data' : admission_data,
        'search'         : search,
        'selected_course': course,
        'selected_batch' : batch,
        'courses'        : Course.objects.filter(is_active=True),
        'batches'        : Batch.objects.filter(is_active=True),
        'total_count'    : admissions.count(),
    })


@login_required
def admission_add(request):
    form = AdmissionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        obj          = form.save(commit=False)
        obj.added_by = request.user
        obj.save()
        if obj.enquiry:
            obj.enquiry.status = 'converted'
            obj.enquiry.save()
        messages.success(request,
            f'Admission for {obj.student.full_name} registered.')
        return redirect('core:admission_list')
    return render(request, 'core/admission_form.html', {
        'form': form, 'title': 'New Admission', 'btn': 'Register Admission'
    })


@login_required
def admission_edit(request, pk):
    obj  = get_object_or_404(Admission, pk=pk)
    form = AdmissionForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Admission updated.')
        return redirect('core:admission_list')
    return render(request, 'core/admission_form.html', {
        'form': form,
        'title': f'Edit — {obj.student.full_name}',
        'btn'  : 'Update Admission'
    })


@login_required
def admission_delete(request, pk):
    obj = get_object_or_404(Admission, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Admission deleted.')
        return redirect('core:admission_list')
    return render(request, 'core/confirm_delete.html', {
        'object_name': str(obj), 'cancel_url': 'core:admission_list'
    })


@login_required
def admission_detail(request, pk):
    obj       = get_object_or_404(Admission, pk=pk)
    fees_list = obj.fees_records.all().order_by('-payment_date')
    return render(request, 'core/admission_detail.html', {
        'admission'    : obj,
        'fees_list'    : fees_list,
        'fees_paid'    : obj.fees_paid,
        'fees_pending' : obj.fees_pending,
        'is_fully_paid': obj.is_fully_paid,
    })


# Print admission form
@login_required
def admission_print(request, pk):
    obj = get_object_or_404(Admission, pk=pk)
    return render(request, 'core/admission_print.html', {'admission': obj})


# ═══════════════════════════════════════════════
# FEES VIEWS
# ═══════════════════════════════════════════════
@login_required
def fees_list(request):
    fees         = Fees.objects.select_related(
                       'admission__student', 'admission__course'
                   ).all()
    search       = request.GET.get('search', '')
    payment_mode = request.GET.get('payment_mode', '')
    payment_type = request.GET.get('payment_type', '')
    if search:
        fees = fees.filter(
            Q(admission__student__full_name__icontains=search)    |
            Q(admission__student__student_id__icontains=search)   |
            Q(course_name__icontains=search)                      |
            Q(receipt_number__icontains=search)
        )
    if payment_mode:
        fees = fees.filter(payment_mode=payment_mode)
    if payment_type:
        fees = fees.filter(payment_type=payment_type)
    return render(request, 'core/fees_list.html', {
        'fees'                 : fees,
        'search'               : search,
        'selected_payment_mode': payment_mode,
        'selected_payment_type': payment_type,
        'payment_mode_choices' : Fees.PAYMENT_MODE_CHOICES,
        'payment_type_choices' : Fees.INSTALLMENT_CHOICES,
        'total_collected'      : fees.aggregate(t=Sum('amount_paid'))['t'] or 0,
        'total_count'          : fees.count(),
    })


@login_required
def fees_add(request):
    form               = FeesForm(request.POST or None)
    previous_payments  = []
    selected_admission = None

    # if admission is selected (via GET or POST), load previous transactions
    admission_id = request.POST.get('admission') or request.GET.get('admission')
    if admission_id:
        try:
            selected_admission = Admission.objects.select_related(
                'student', 'course'
            ).get(pk=admission_id)
            previous_payments = selected_admission.fees_records.order_by(
                '-payment_date'
            )
        except Admission.DoesNotExist:
            pass

    if request.method == 'POST' and form.is_valid():
        obj              = form.save(commit=False)
        obj.collected_by = request.user
        obj.save()
        messages.success(request,
            f'Payment ₹{obj.amount_paid} collected. '
            f'Receipt: {obj.receipt_number}. '
            f'Remaining: ₹{obj.remaining_fees}')
        return redirect('core:fees_list')

    return render(request, 'core/fees_form.html', {
        'form'              : form,
        'title'             : 'Collect Fees',
        'btn'               : 'Save Payment',
        'previous_payments' : previous_payments,
        'selected_admission': selected_admission,
    })


@login_required
def fees_edit(request, pk):
    obj  = get_object_or_404(Fees, pk=pk)
    form = FeesForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Fee record updated.')
        return redirect('core:fees_list')
    return render(request, 'core/fees_form.html', {
        'form': form,
        'title': f'Edit — {obj.admission.student.full_name}',
        'btn'  : 'Update Payment',
        'previous_payments': obj.admission.fees_records.exclude(
            pk=pk
        ).order_by('-payment_date'),
        'selected_admission': obj.admission,
    })


@login_required
def fees_delete(request, pk):
    obj = get_object_or_404(Fees, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Fee record deleted.')
        return redirect('core:fees_list')
    return render(request, 'core/confirm_delete.html', {
        'object_name': f'{obj.receipt_number} — ₹{obj.amount_paid}',
        'cancel_url' : 'core:fees_list'
    })


@login_required
def fees_detail(request, pk):
    return render(request, 'core/fees_detail.html', {
        'fee': get_object_or_404(Fees, pk=pk)
    })


# Print fee receipt
@login_required
def fee_receipt_print(request, pk):
    fee = get_object_or_404(Fees, pk=pk)
    return render(request, 'core/fee_receipt_print.html', {'fee': fee})


# AJAX — load previous payments when admission selected in fees form
@login_required
def get_admission_payments(request):
    admission_id = request.GET.get('admission_id')
    try:
        admission = Admission.objects.select_related(
            'student', 'course'
        ).get(pk=admission_id)
        payments = list(admission.fees_records.order_by('-payment_date').values(
            'receipt_number', 'amount_paid', 'remaining_fees',
            'payment_date', 'payment_mode', 'payment_type'
        ))
        return JsonResponse({
            'found'        : True,
            'student_name' : admission.student.full_name,
            'student_id'   : admission.student.student_id,
            'course'       : str(admission.course),
            'total_fees'   : float(admission.total_fees),
            'fees_paid'    : float(admission.fees_paid),
            'fees_pending' : float(admission.fees_pending),
            'payments'     : payments,
        })
    except Admission.DoesNotExist:
        return JsonResponse({'found': False})


# ═══════════════════════════════════════════════
# COURSE & BATCH MASTER DATA VIEWS
# ═══════════════════════════════════════════════
@login_required
def course_list(request):
    return render(request, 'core/course_list.html', {
        'courses': Course.objects.all()
    })


@login_required
def course_add(request):
    form = CourseForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Course added.')
        return redirect('core:course_list')
    return render(request, 'core/course_form.html', {
        'form': form, 'title': 'Add Course', 'btn': 'Save Course'
    })


@login_required
def course_edit(request, pk):
    obj  = get_object_or_404(Course, pk=pk)
    form = CourseForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Course updated.')
        return redirect('core:course_list')
    return render(request, 'core/course_form.html', {
        'form': form, 'title': 'Edit Course', 'btn': 'Update Course'
    })


@login_required
def batch_list(request):
    return render(request, 'core/batch_list.html', {
        'batches': Batch.objects.all()
    })


@login_required
def batch_add(request):
    form = BatchForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Batch added.')
        return redirect('core:batch_list')
    return render(request, 'core/batch_form.html', {
        'form': form, 'title': 'Add Batch', 'btn': 'Save Batch'
    })


@login_required
def batch_edit(request, pk):
    obj  = get_object_or_404(Batch, pk=pk)
    form = BatchForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Batch updated.')
        return redirect('core:batch_list')
    return render(request, 'core/batch_form.html', {
        'form': form, 'title': 'Edit Batch', 'btn': 'Update Batch'
    })


# ═══════════════════════════════════════════════
# REPORTS
# ═══════════════════════════════════════════════
@login_required
def reports(request):
    today = timezone.now().date()
    month = int(request.GET.get('month', today.month))
    year  = int(request.GET.get('year',  today.year))

    # filtered month-wise data
    admissions_monthly = (
        Admission.objects
        .filter(admission_date__month=month, admission_date__year=year)
        .select_related('student', 'course')
    )
    fees_monthly = (
        Fees.objects
        .filter(payment_date__month=month, payment_date__year=year)
        .select_related('admission__student')
    )

    all_admissions      = Admission.objects.select_related('student', 'course').all()
    pending_students    = [
        {'admission': a, 'fees_paid': a.fees_paid, 'fees_pending': a.fees_pending}
        for a in all_admissions if a.fees_pending > 0
    ]
    fully_paid_students = [a for a in all_admissions if a.is_fully_paid]

    reference_stats    = Enquiry.objects.values('reference').annotate(count=Count('id')).order_by('-count')
    status_stats       = Enquiry.objects.values('status').annotate(count=Count('id')).order_by('-count')
    course_stats       = Admission.objects.values('course__name').annotate(count=Count('id')).order_by('-count')
    payment_mode_stats = Fees.objects.values('payment_mode').annotate(total=Sum('amount_paid'), count=Count('id')).order_by('-total')
    installment_stats  = Fees.objects.values('payment_type').annotate(count=Count('id'), total=Sum('amount_paid'))
    gender_stats       = Student.objects.values('gender').annotate(count=Count('id'))

    total_fees_charged   = sum(a.total_fees for a in all_admissions)
    total_fees_collected = Fees.objects.aggregate(t=Sum('amount_paid'))['t'] or 0

    # month dropdown options (last 12 months)
    import calendar
    from datetime import timedelta
    month_choices = []
    for i in range(11, -1, -1):
        d = today.replace(day=1) - timedelta(days=30 * i)
        month_choices.append({
            'month': d.month, 'year': d.year,
            'label': d.strftime('%B %Y')
        })

    context = {
        'admissions_monthly'   : admissions_monthly,
        'fees_monthly'         : fees_monthly,
        'pending_students'     : pending_students,
        'fully_paid_students'  : fully_paid_students,
        'pending_count'        : len(pending_students),
        'fully_paid_count'     : len(fully_paid_students),
        'reference_stats'      : reference_stats,
        'status_stats'         : status_stats,
        'course_stats'         : course_stats,
        'payment_mode_stats'   : payment_mode_stats,
        'installment_stats'    : installment_stats,
        'gender_stats'         : gender_stats,
        'total_fees_charged'   : total_fees_charged,
        'total_fees_collected' : total_fees_collected,
        'total_fees_pending'   : total_fees_charged - total_fees_collected,
        'month_choices'        : month_choices,
        'selected_month'       : month,
        'selected_year'        : year,
    }
    return render(request, 'core/reports.html', context)


# ═══════════════════════════════════════════════
# ERROR PAGES
# ═══════════════════════════════════════════════
def error_404(request, exception):
    return render(request, 'core/404.html', status=404)

def error_500(request):
    return render(request, 'core/500.html', status=500)