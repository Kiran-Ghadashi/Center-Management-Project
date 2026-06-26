from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Student, Enquiry, Admission, Fees, Course, Batch


# ─────────────────────────────────────────
# AUTH FORMS
# ─────────────────────────────────────────
class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True)
    class Meta:
        model  = User
        fields = ['username', 'email', 'password1', 'password2']


# ─────────────────────────────────────────
# STUDENT FORM
# ─────────────────────────────────────────
class StudentForm(forms.ModelForm):
    class Meta:
        model   = Student
        exclude = ['student_id', 'created_at']
        widgets = {
            'full_name' : forms.TextInput(attrs={'placeholder': 'Enter full name'}),
            'phone'     : forms.TextInput(attrs={'placeholder': '10-digit mobile number'}),
            'email'     : forms.EmailInput(attrs={'placeholder': 'Email (optional)'}),
            'gender'    : forms.Select(),
            'address'   : forms.Textarea(attrs={'rows': 2, 'placeholder': 'Address (optional)'}),
            'photo'     : forms.ClearableFileInput(attrs={'accept': 'image/*'}),
            'signature' : forms.ClearableFileInput(attrs={'accept': 'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required     = False
        self.fields['address'].required   = False
        self.fields['photo'].required     = False
        self.fields['signature'].required = False

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone.isdigit() or len(phone) != 10:
            raise forms.ValidationError('Enter a valid 10-digit mobile number.')
        return phone


# ─────────────────────────────────────────
# ENQUIRY FORM
# ─────────────────────────────────────────
class EnquiryForm(forms.ModelForm):

    class Meta:
        model   = Enquiry
        exclude = ['added_by', 'enquiry_date']
        widgets = {
            'student'          : forms.Select(),
            'student_name'     : forms.TextInput(attrs={'placeholder': 'Full name'}),
            'phone'            : forms.TextInput(attrs={'placeholder': '10-digit mobile'}),
            'email'            : forms.EmailInput(attrs={'placeholder': 'Email (optional)'}),
            'course_interested': forms.TextInput(attrs={'placeholder': 'e.g. Python, Tally'}),
            'reference'        : forms.Select(),
            'status'           : forms.Select(),
            'notes'            : forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['student'].required   = False
        self.fields['email'].required     = False
        self.fields['notes'].required     = False
        self.fields['student'].empty_label = '-- Select Existing Student (optional) --'
        self.fields['student'].label_from_instance = lambda obj: (
            f'{obj.student_id} — {obj.full_name} ({obj.phone})'
        )
        # hint text
        self.fields['student'].help_text = (
            'If student already exists select here — '
            'name and phone will auto-fill.'
        )


# ─────────────────────────────────────────
# ADMISSION FORM
# ─────────────────────────────────────────
class AdmissionForm(forms.ModelForm):

    admission_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    class Meta:
        model   = Admission
        exclude = ['added_by']
        widgets = {
            'student'    : forms.Select(),
            'course'     : forms.Select(),
            'batch'      : forms.Select(),
            'total_fees' : forms.NumberInput(attrs={'placeholder': 'Total fees ₹'}),
            'enquiry'    : forms.Select(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['enquiry'].required   = False
        self.fields['enquiry'].empty_label = '-- Link Enquiry (optional) --'
        self.fields['student'].empty_label = '-- Select Student --'
        self.fields['course'].empty_label  = '-- Select Course --'
        self.fields['batch'].empty_label   = '-- Select Batch --'

        # only active courses and batches
        self.fields['course'].queryset = Course.objects.filter(is_active=True)
        self.fields['batch'].queryset  = Batch.objects.filter(is_active=True)

        # enquiry dropdown — only pending/followup
        self.fields['enquiry'].queryset = Enquiry.objects.filter(
            status__in=['pending', 'followup']
        )
        self.fields['student'].label_from_instance = lambda obj: (
            f'{obj.student_id} — {obj.full_name} ({obj.phone})'
        )
        self.fields['enquiry'].label_from_instance = lambda obj: (
            f'{obj.student_name} | {obj.course_interested} | {obj.phone}'
        )

    def clean_total_fees(self):
        fees = self.cleaned_data.get('total_fees')
        if fees is not None and fees <= 0:
            raise forms.ValidationError('Total fees must be greater than 0.')
        return fees


# ─────────────────────────────────────────
# FEES FORM
# ─────────────────────────────────────────
class FeesForm(forms.ModelForm):

    payment_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    class Meta:
        model   = Fees
        # receipt_number, course_name, remaining_fees are auto-generated
        exclude = ['collected_by', 'receipt_number', 'course_name', 'remaining_fees']
        widgets = {
            'admission'    : forms.Select(),
            'payment_type' : forms.Select(),
            'amount_paid'  : forms.NumberInput(attrs={'placeholder': 'Amount ₹'}),
            'payment_mode' : forms.Select(),
            'remarks'      : forms.Textarea(attrs={'rows': 2, 'placeholder': 'Optional...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['remarks'].required = False

        # show student id + name + course + pending amount
        all_admissions    = Admission.objects.select_related('student', 'course').all()
        pending_ids       = [a.pk for a in all_admissions if a.fees_pending > 0]
        self.fields['admission'].queryset = Admission.objects.filter(
            pk__in=pending_ids
        ).select_related('student', 'course')
        self.fields['admission'].empty_label = '-- Select Student --'
        self.fields['admission'].label_from_instance = lambda obj: (
            f'{obj.student.student_id} — {obj.student.full_name} | '
            f'{obj.course} | Pending: ₹{obj.fees_pending}'
        )

    def clean_amount_paid(self):
        amount    = self.cleaned_data.get('amount_paid')
        admission = self.cleaned_data.get('admission')
        if amount is not None and amount <= 0:
            raise forms.ValidationError('Amount must be greater than 0.')
        if admission and amount and amount > admission.fees_pending:
            raise forms.ValidationError(
                f'Amount ₹{amount} exceeds pending fees ₹{admission.fees_pending}.'
            )
        return amount


# ─────────────────────────────────────────
# COURSE & BATCH FORMS (for master data)
# ─────────────────────────────────────────
class CourseForm(forms.ModelForm):
    class Meta:
        model   = Course
        fields  = ['name', 'duration', 'fees', 'is_active']
        widgets = {
            'name'     : forms.TextInput(attrs={'placeholder': 'e.g. Python Full Stack'}),
            'duration' : forms.TextInput(attrs={'placeholder': 'e.g. 3 Months'}),
            'fees'     : forms.NumberInput(attrs={'placeholder': 'Course fees ₹'}),
        }


class BatchForm(forms.ModelForm):
    class Meta:
        model   = Batch
        fields  = ['name', 'timing', 'is_active']
        widgets = {
            'name'   : forms.TextInput(attrs={'placeholder': 'e.g. Morning Batch'}),
            'timing' : forms.TextInput(attrs={'placeholder': 'e.g. 9:00 AM - 11:00 AM'}),
        }