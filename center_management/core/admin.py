from django.contrib import admin
from .models import Student, Enquiry, Admission, Fees, Course, Batch


# ─────────────────────────────────────────
# STUDENT ADMIN
# ─────────────────────────────────────────
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display  = ['student_id', 'full_name', 'phone', 'gender', 'created_at']
    list_filter   = ['gender']
    search_fields = ['student_id', 'full_name', 'phone', 'email']
    ordering      = ['-created_at']
    readonly_fields = ['student_id', 'created_at']


# ─────────────────────────────────────────
# COURSE ADMIN
# ─────────────────────────────────────────
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display  = ['name', 'duration', 'fees', 'is_active']
    list_filter   = ['is_active']
    search_fields = ['name']
    list_editable = ['is_active']


# ─────────────────────────────────────────
# BATCH ADMIN
# ─────────────────────────────────────────
@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display  = ['name', 'timing', 'is_active']
    list_filter   = ['is_active']
    search_fields = ['name']
    list_editable = ['is_active']


# ─────────────────────────────────────────
# ENQUIRY ADMIN
# ─────────────────────────────────────────
@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin):

    list_display  = [
        'student_name', 'phone', 'course_interested',
        'reference', 'status', 'enquiry_date', 'added_by'
    ]
    list_filter   = ['status', 'reference', 'enquiry_date']
    search_fields = ['student_name', 'phone', 'course_interested']
    list_editable = ['status']
    ordering      = ['-enquiry_date']

    fieldsets = (
        ('Student Information', {
            'fields': ('student', 'student_name', 'phone', 'email')
        }),
        ('Enquiry Details', {
            'fields': ('course_interested', 'reference', 'status', 'notes')
        }),
        ('Meta', {
            'fields': ('added_by',),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.added_by = request.user
        super().save_model(request, obj, form, change)


# ─────────────────────────────────────────
# FEES INLINE — shown inside Admission page
# ─────────────────────────────────────────
class FeesInline(admin.TabularInline):
    model           = Fees
    extra           = 1
    readonly_fields = ['receipt_number', 'course_name', 'remaining_fees', 'collected_by']
    fields          = [
        'payment_type', 'amount_paid', 'payment_date',
        'payment_mode', 'receipt_number', 'course_name',
        'remaining_fees', 'remarks'
    ]


# ─────────────────────────────────────────
# ADMISSION ADMIN
# ─────────────────────────────────────────
@admin.register(Admission)
class AdmissionAdmin(admin.ModelAdmin):

    # ✅ Use 'student__full_name', 'student__phone', 'student__gender'
    #    since these fields live on the related Student model
    list_display  = [
        'get_student_name', 'get_student_phone', 'get_student_gender',
        'course', 'batch', 'admission_date', 'total_fees',
        'fees_paid_display', 'fees_pending_display', 'added_by'
    ]

    # ✅ 'gender' is on Student, not Admission — use student__gender
    list_filter   = ['course', 'batch', 'student__gender', 'admission_date']

    # ✅ Search via related Student fields using double underscore
    search_fields = ['student__full_name', 'student__phone', 'course__name', 'batch__name']

    ordering      = ['-admission_date']
    inlines       = [FeesInline]

    fieldsets = (
        ('Student', {
            'fields': ('student',)
        }),
        ('Course Information', {
            'fields': ('course', 'batch', 'admission_date', 'total_fees', 'enquiry')
        }),
        ('Meta', {
            'fields': ('added_by',),
            'classes': ('collapse',)
        }),
    )

    # ── Custom column methods (accessing related Student fields) ──

    @admin.display(description='Student Name', ordering='student__full_name')
    def get_student_name(self, obj):
        return obj.student.full_name

    @admin.display(description='Phone', ordering='student__phone')
    def get_student_phone(self, obj):
        return obj.student.phone

    @admin.display(description='Gender', ordering='student__gender')
    def get_student_gender(self, obj):
        return obj.student.get_gender_display()

    @admin.display(description='Fees Paid')
    def fees_paid_display(self, obj):
        return f'₹{obj.fees_paid}'

    @admin.display(description='Fees Pending')
    def fees_pending_display(self, obj):
        return f'₹{obj.fees_pending}'

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.added_by = request.user
        super().save_model(request, obj, form, change)


# ─────────────────────────────────────────
# FEES ADMIN
# ─────────────────────────────────────────
@admin.register(Fees)
class FeesAdmin(admin.ModelAdmin):

    list_display  = [
        'receipt_number', 'get_student_name', 'course_name', 'payment_type',
        'amount_paid', 'remaining_fees', 'payment_mode',
        'payment_date', 'collected_by'
    ]
    list_filter   = ['payment_mode', 'payment_type', 'payment_date']

    # ✅ Fixed: was 'admission__student_name' — correct is 'admission__student__full_name'
    search_fields = ['admission__student__full_name', 'course_name', 'receipt_number']

    ordering      = ['-payment_date']
    readonly_fields = ['receipt_number', 'course_name', 'remaining_fees']

    fieldsets = (
        ('Payment Information', {
            'fields': (
                'admission', 'payment_type', 'amount_paid',
                'payment_date', 'payment_mode', 'receipt_number'
            )
        }),
        ('Auto Calculated', {
            'fields': ('course_name', 'remaining_fees'),
            'description': 'These fields are calculated automatically on save.'
        }),
        ('Extra', {
            'fields': ('remarks', 'collected_by'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description='Student Name', ordering='admission__student__full_name')
    def get_student_name(self, obj):
        return obj.admission.student.full_name

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.collected_by = request.user
        super().save_model(request, obj, form, change)