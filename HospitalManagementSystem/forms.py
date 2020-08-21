from .models import (
    Address,
    AppUser,
    Certificate,
    PatientPersonalReccord,
    PatientHealthReccord,
    DepartmentInventory,
    PurchaseList,
    HealthRemarks,
    Prescription,
    TestResults,
    Test,
    SurgeryDocuments,
    Surgery,
    Admission,
    PatientUnknown,
    StaffReport,
    EMessage,
    Department,
    DepartmentManager,
    Inventory,
    Fatality,
    HumanOrgan,
    Level
)
from django.contrib.auth.forms import UserCreationForm
from django.forms import inlineformset_factory
from django.contrib.auth.models import User
from django import forms


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, help_text="Required.")
    last_name = forms.CharField(max_length=30, help_text="Required.")
    email = forms.EmailField(
        max_length=254, help_text="Required. Inform a valid email address."
    )

    class Meta:
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
        )


class ChangeUserDetailsForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')    


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ("place", "zip_code", "district")


class UserFormForApp(forms.ModelForm):
    pro_level = forms.ModelChoiceField(queryset=Level.objects.filter(level_number__gt = 3))
    class Meta:
        model = AppUser
        fields = (
            "age",
            "department",
            "phone",
            "qualifications",
            "shift",
        )

class QUploadForm(forms.ModelForm):
    class Meta:
        model = Certificate
        fields = (
            "certificate_title",
            "photo",
        )


class PatientPersonalRecordForm(forms.ModelForm):
    class Meta:
        model = PatientPersonalReccord
        fields = ("p_Fname", "p_Lname", "p_age", "phone", "p_gender", "photo")


class PatientHealthReccordForm(forms.ModelForm):
    class Meta:
        model = PatientHealthReccord
        fields = ("departments", "accident", "companion_name", "companion_phone")


class InventoryListForm(forms.ModelForm):
    class Meta:
        model = DepartmentInventory
        fields = (
            "item",
            "count",
        )


class HealthRemarkForm(forms.ModelForm):
    class Meta:
        model = HealthRemarks
        fields = ("rem_text",)
        exclude = ()


class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ("medicine", "med_number", "med_freq")


class TestForm(forms.ModelForm):
    class Meta:
        model = TestResults
        fields = ("test",)


class SurgeryDocsForm(forms.ModelForm):
    class Meta:
        model = SurgeryDocuments
        fields = ("title", "photo")


class SurgeyPrepayForm(forms.ModelForm):
    prepay_amount = forms.DecimalField(label="paying amount", initial=0)

    class Meta:
        model = Surgery
        fields = ("is_prepaid",)


class AddDiseaseForm(forms.ModelForm):
    class Meta:
        model = PatientHealthReccord
        fields = ("diseases",)


class AddTestsForm(forms.Form):
    tests = forms.ModelMultipleChoiceField(queryset=Test.objects.all(), required=False)


class AddRemarkForm(forms.ModelForm):
    class Meta:
        model = HealthRemarks
        fields = ('rem_text',)


class StaffReportForm(forms.ModelForm):
    staff = forms.ModelChoiceField(queryset=None)

    class Meta:
        model = StaffReport
        fields = ("remark",)

    def __init__(self, au, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if au.pro_level.level_number < 4:
            q = AppUser.objects.filter(id__in = DepartmentManager.objects.all().values('manager__id'))
        else:
            dep = au.department
            de_mans = dep.departmentmanager_set.values("manager")
            q = dep.appuser_set.exclude(id__in=de_mans)
        self.fields["staff"].queryset = q


class AttendanceRegistrationForm(forms.Form):
    username = forms.CharField()
    password = forms.PasswordInput()


class DepartmentMessageForm(forms.ModelForm):
    reciever = forms.ModelChoiceField(queryset= Department.objects.all())
    class Meta:
        model = EMessage
        fields = [
            "subject",
            "text",
        ]

class ChangeDepartmentForm(forms.Form):
    new_dep = forms.ModelChoiceField(queryset= Department.objects.filter(is_medical = True))


class InventorySubForm(forms.ModelForm):
    class Meta:
        model = Inventory
        fields = ('item', 'description')

class FatalityForm(forms.ModelForm):
    class Meta:
        model = Fatality
        fields = ['date_of', 'time_of', 'cause', 'cause_description', 'death_report']

class DeceasedCompanionForm(forms.ModelForm):
    class Meta:
        model = PatientHealthReccord
        fields = ("companion_name", "companion_phone", "accident")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["companion_name"].required = True
        self.fields["companion_phone"].required = True


class SurgeryWritingForm(forms.ModelForm):
    class Meta:
        model = Surgery
        fields = ('end_date', 'end_time', 'surgery_report')

class HumanOrganForm(forms.ModelForm):
    organ_class = forms.ChoiceField(choices=((0, 'highly critical organ'), (1, 'critical organ'), (2, 'important organ'), (3, 'internal organ'), (4, 'external organ')))
    class Meta:
        model = HumanOrgan
        fields = ('organ_name', 'organ_description', 'photo', 'related_organs')
