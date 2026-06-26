from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


# ─────────────────────────────────────────
# STUDENT MODEL (Central student record)
# ─────────────────────────────────────────
class Student(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]

    student_id   = models.CharField(max_length=20, unique=True, editable=False)
    full_name    = models.CharField(max_length=100)
    phone        = models.CharField(max_length=15)
    email        = models.EmailField(blank=True)
    gender       = models.CharField(max_length=10, choices=GENDER_CHOICES, default='male')
    photo        = models.ImageField(upload_to='students/photos/', blank=True, null=True)
    signature    = models.ImageField(upload_to='students/signatures/', blank=True, null=True)
    address      = models.TextField(blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Auto-generate student ID like STU-0001, STU-0002 ...
        if not self.student_id:
            last = Student.objects.order_by('id').last()
            next_id = (last.id + 1) if last else 1
            self.student_id = f'STU-{next_id:04d}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.student_id} — {self.full_name}'

    class Meta:
        ordering = ['-created_at']


# ─────────────────────────────────────────
# ENQUIRY MODEL
# ─────────────────────────────────────────
class Enquiry(models.Model):

    STATUS_CHOICES = [
        ('pending',   'Pending'),
        ('followup',  'Follow Up'),
        ('converted', 'Converted'),
        ('closed',    'Closed'),
    ]
    REFERENCE_CHOICES = [
        ('friend',        'Friend'),
        ('social_media',  'Social Media'),
        ('advertisement', 'Advertisement'),
        ('school',        'School'),
        ('coaching',      'Coaching'),
        ('other',         'Other'),
    ]

    # Link to student — if student already exists, pick them
    # If new student, leave blank and fill name/phone manually
    student           = models.ForeignKey(
                            Student, on_delete=models.SET_NULL,
                            null=True, blank=True,
                            related_name='enquiries'
                        )
    # These are used when student record doesn't exist yet
    student_name      = models.CharField(max_length=100)
    phone             = models.CharField(max_length=15)
    email             = models.EmailField(blank=True)

    course_interested = models.CharField(max_length=100)
    reference         = models.CharField(max_length=20, choices=REFERENCE_CHOICES, default='friend')
    status            = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    enquiry_date      = models.DateField(auto_now_add=True)
    notes             = models.TextField(blank=True)
    added_by          = models.ForeignKey(
                            User, on_delete=models.SET_NULL,
                            null=True, related_name='enquiries_added'
                        )

    def __str__(self):
        return f'{self.student_name} — {self.course_interested}'

    class Meta:
        verbose_name_plural = 'Enquiries'
        ordering = ['-enquiry_date']


# ─────────────────────────────────────────
# COURSE MODEL (dropdown master data)
# ─────────────────────────────────────────
class Course(models.Model):
    name       = models.CharField(max_length=100, unique=True)
    duration   = models.CharField(max_length=50, blank=True,
                                  help_text='e.g. 3 Months, 6 Months')
    fees       = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active  = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


# ─────────────────────────────────────────
# BATCH MODEL (dropdown master data)
# ─────────────────────────────────────────
class Batch(models.Model):
    name       = models.CharField(max_length=100)
    timing     = models.CharField(max_length=50, blank=True,
                                  help_text='e.g. 9:00 AM - 11:00 AM')
    is_active  = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.name} ({self.timing})' if self.timing else self.name

    class Meta:
        ordering = ['name']


# ─────────────────────────────────────────
# ADMISSION MODEL
# ─────────────────────────────────────────
class Admission(models.Model):

    student        = models.ForeignKey(
                         Student, on_delete=models.CASCADE,
                         related_name='admissions'
                     )
    course         = models.ForeignKey(
                         Course, on_delete=models.SET_NULL,
                         null=True, related_name='admissions'
                     )
    batch          = models.ForeignKey(
                         Batch, on_delete=models.SET_NULL,
                         null=True, related_name='admissions'
                     )
    admission_date = models.DateField()
    total_fees     = models.DecimalField(max_digits=10, decimal_places=2)
    enquiry        = models.ForeignKey(
                         Enquiry, on_delete=models.SET_NULL,
                         null=True, blank=True, related_name='admissions'
                     )
    added_by       = models.ForeignKey(
                         User, on_delete=models.SET_NULL,
                         null=True, related_name='admissions_added'
                     )

    def __str__(self):
        return f'{self.student.full_name} — {self.course}'

    @property
    def fees_paid(self):
        return self.fees_records.aggregate(
            total=models.Sum('amount_paid')
        )['total'] or 0

    @property
    def fees_pending(self):
        return self.total_fees - self.fees_paid

    @property
    def is_fully_paid(self):
        return self.fees_pending <= 0

    class Meta:
        ordering = ['-admission_date']
        # one student can enroll in same course only once at a time
        unique_together = ['student', 'course']


# ─────────────────────────────────────────
# FEES MODEL
# ─────────────────────────────────────────
class Fees(models.Model):

    PAYMENT_MODE_CHOICES = [
        ('cash',          'Cash'),
        ('upi',           'UPI'),
        ('bank_transfer', 'Bank Transfer'),
        ('cheque',        'Cheque'),
    ]
    INSTALLMENT_CHOICES = [
        ('full',         'Full Payment'),
        ('installment',  'Installment'),
    ]

    admission       = models.ForeignKey(
                          Admission, on_delete=models.CASCADE,
                          related_name='fees_records'
                      )
    receipt_number  = models.CharField(max_length=50, unique=True,
                                       editable=False)
    course_name     = models.CharField(max_length=100)
    payment_type    = models.CharField(max_length=15,
                                       choices=INSTALLMENT_CHOICES,
                                       default='full')
    amount_paid     = models.DecimalField(max_digits=10, decimal_places=2)
    remaining_fees  = models.DecimalField(max_digits=10, decimal_places=2,
                                          default=0.00)
    payment_date    = models.DateField()
    payment_mode    = models.CharField(max_length=20,
                                       choices=PAYMENT_MODE_CHOICES)
    remarks         = models.TextField(blank=True)
    collected_by    = models.ForeignKey(
                          User, on_delete=models.SET_NULL,
                          null=True, related_name='fees_collected'
                      )

    def save(self, *args, **kwargs):
        # Auto-generate receipt number like RCP-2024-0001
        if not self.receipt_number:
            year  = timezone.now().year
            last  = Fees.objects.filter(
                        receipt_number__startswith=f'RCP-{year}-'
                    ).order_by('id').last()
            if last:
                last_num = int(last.receipt_number.split('-')[-1])
                next_num = last_num + 1
            else:
                next_num = 1
            self.receipt_number = f'RCP-{year}-{next_num:04d}'

        # Auto-fill course name
        if self.admission and not self.course_name:
            self.course_name = str(self.admission.course)

        # Auto-calculate remaining fees
        total_paid_before = self.admission.fees_records.exclude(
            pk=self.pk
        ).aggregate(total=models.Sum('amount_paid'))['total'] or 0

        self.remaining_fees = max(
            self.admission.total_fees - total_paid_before - self.amount_paid,
            0
        )
        super().save(*args, **kwargs)

    def __str__(self):
        return (f'{self.receipt_number} | '
                f'{self.admission.student.full_name} | '
                f'₹{self.amount_paid}')

    class Meta:
        verbose_name_plural = 'Fees'
        ordering = ['-payment_date']