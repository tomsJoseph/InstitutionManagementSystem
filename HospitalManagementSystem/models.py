from django.http import Http404, HttpResponse, HttpResponseForbidden
from datetime import datetime, timedelta, timezone, time
from django.contrib.auth.models import User
from .helpers import serialize_qs
from django.db.models import Sum, F
from django.db import models
from decimal import Decimal
from .Address import *
import calendar


class HumanOrgan(models.Model):
    organ_name = models.CharField(max_length=30)
    organ_class = models.IntegerField()
    organ_description = models.TextField(max_length=300)
    related_organs = models.ManyToManyField('HumanOrgan', blank=True)
    photo = models.FileField(upload_to="organs", null=True, blank=True)

    def __str__(self):
        return self.organ_name

    def classification(self):
        all_classes = ['highly critical','critical', 'important', 'internal', 'external']
        return all_classes[self.organ_class]


class Shift(models.Model):
    shift_name = models.CharField(max_length=10)
    start_time = models.TimeField()
    end_time = models.TimeField()
    last_updated = models.DateTimeField(auto_now=True, null=True)
    next_turn = models.ForeignKey("self", null=True, on_delete=models.CASCADE, blank=True)

    def __str__(self):
        return (
            "Shift "
            + self.shift_name
            + " "
            + str(self.start_time)
            + " - "
            + str(self.end_time)
        )

    def shift_change_due(self):
        from django.utils import timezone

        a = (self.last_updated - timezone.now()).total_seconds()
        return a > 60 * 60 * 24

    def current_shift():
        h = datetime.now()
        sh = Shift.objects.filter(start_time__lt=h, end_time__gt=h)
        if not sh:
            sh = Shift.objects.filter(start_time__lt=h, end_time=time(0))
        return sh[0]

    def predict_shift_change():
        class dummy_shift:
            pass

        ds1 = dummy_shift()
        ds2 = dummy_shift()
        ds3 = dummy_shift()

        shifts = Shift.objects.all()

        shift_dict = serialize_qs(shifts, ["shift_name", "start_time", "end_time"])

        sh = shifts.get(end_time=time(16))
        ds1.shift_name = sh.shift_name
        ds1.start_time = sh.start_time
        ds1.end_time = time(5)

        sh = shifts.get(end_time=time(0))
        ds2.shift_name = sh.shift_name
        ds2.end_time = time(16)
        ds2.start_time = time(8)

        sh = shifts.get(end_time=time(8))
        ds3.shift_name = sh.shift_name
        ds3.end_time = time(0)
        ds3.start_time = time(16)

        ds1.end_time = time(8)
        ds1.start_time = time(0)

        a = Shift.objects.get(shift_name=ds1.shift_name)
        a.next_turn = Shift.objects.get(
            start_time=ds1.start_time, end_time=ds1.end_time
        )

        b = Shift.objects.get(shift_name=ds2.shift_name)
        b.next_turn = Shift.objects.get(
            start_time=ds2.start_time, end_time=ds2.end_time
        )

        c = Shift.objects.get(shift_name=ds3.shift_name)
        c.next_turn = Shift.objects.get(
            start_time=ds3.start_time, end_time=ds3.end_time
        )

        a.save()
        b.save()
        c.save()


class Hospital(models.Model):
    h_name = models.CharField(max_length=30)
    h_address = models.ForeignKey(Address, null=True, on_delete=models.SET_NULL)
    phone1 = models.IntegerField()
    phone2 = models.IntegerField()
    email = models.CharField(max_length=30)

    def __str__(self):
        return self.h_name


class Department(models.Model):
    department_name = models.CharField(max_length=15)
    department_description = models.CharField(max_length=50)
    is_medical = models.BooleanField(default=True)

    def __str__(self):
        return self.department_name

    def all_cases(self, years):
        cases = []
        count = 0
        for year in years:
            avl_cases = self.patienthealthreccord_set.filter(op_time_stamp__year=year)
            if avl_cases:
                cases.append(
                    (
                        year,
                        self.patienthealthreccord_set.filter(
                            op_time_stamp__year=year
                        ).count(),
                    )
                )
                count += avl_cases.count()

        return (cases, count)

    def year_cases(self, year):
        cases = []

        avl_cases = self.patienthealthreccord_set.filter(
            op_time_stamp__year=year
        )
        if avl_cases:
            for mon in range(1, 13):
                mnth_cases = avl_cases.filter(
                    op_time_stamp__month=mon
                )
                cases.append((calendar.month_name[mon], mnth_cases.count()))

        count = avl_cases.count()

        return (cases, count)

    def all_complaints(self, years):
        complaints = []
        ccount = fcount = 0
        for year in years:
            avl_complaints = self.complaintsfeedback_set.filter(time_filed__year=year)
            complaints.append(
                (
                    year,
                    avl_complaints.filter(is_compaint=True).count(),
                    avl_complaints.filter(is_compaint=False).count(),
                )
            )
            ccount += complaints[-1][1]
            fcount += complaints[-1][2]

        return (complaints, (ccount, fcount))

    def year_complaints(self, year):
        complaints = []
        fcount = 0
        avl_complaints = self.complaintsfeedback_set.filter(
            time_filed__year=year
        )
        for mon in range(1, 13):
            mnth_complaints = avl_complaints.filter(
                time_filed__month=mon
            )
            complaints.append(
                (
                    calendar.month_name[mon],
                    mnth_complaints.filter(is_compaint=True).count(),
                    mnth_complaints.filter(is_compaint=False).count(),
                )
            )
            fcount += complaints[-1][1]

        ccount = avl_complaints.count() - fcount

        return (complaints, (fcount, ccount))

    def appoint_manager(self, manager, staff):
        if (staff.department == self) and (self.is_manager(manager)):
            new_man = self.departmentmanager_set.create()
            new_man.manager = staff
            new_man.save()
            self.departmentmanager_set.filter(manager=manager).delete()
            return True
        else:
            return False

    def is_manager(self, staff):
        return DepartmentManager.objects.filter(manager=staff)

    def present_staffs(self):
        return Attendance.objects.select_related("staff__department").filter(
            staff__department=self,
            present=True,
            time_of_attendance__date=datetime.today(),
        )

    def absent_staffs(self):
        present_staffs = [
            at.staff.app_user
            for at in Attendance.objects.select_related("staff__department").filter(
                staff__department=self,
                present=True,
                time_of_attendance__date=datetime.today(),
            )
        ]
        return Attendance.objects.select_related("staff__department").filter(
            staff__department=self,
            present=False,
            time_of_attendance__date=datetime.today(),
        )

    def leaves(self):
        shift = Shift.current_shift()
        return LeaveApplications.objects.select_related("applicant__department", "applicant__shift").filter(
            date__date=datetime.today(),
            applicant__shift = shift,
            applicant__department=self,
            approved=True,
            canceled=False,
        )

    def get_attendances(self):
        reports = []
        appusers = self.appuser_set.all()
        for appuser in appusers:
            reports.append(
                (
                    appuser.app_user.username,
                    appuser.attendance_set.filter(
                        present=False, time_of_attendance__year=datetime.today().year
                    ).count(),
                    appuser.attendance_set.filter(
                        present=False, time_of_attendance__month=datetime.today().month
                    ).count(),
                )
            )
        return reports

    def get_smallest_shift_group(self):
        a = self.appuser_set.select_related("shift__shift_name").filter(
            shift__shift_name="A"
        )
        b = self.appuser_set.select_related("shift__shift_name").filter(
            shift__shift_name="B"
        )
        c = self.appuser_set.select_related("shift__shift_name").filter(
            shift__shift_name="C"
        )

        if a.count() < b.count():
            if a.count() < c.count():
                return Shift.objects.get(shift_name="A")
            else:
                return Shift.objects.get(shift_name="C")
        elif b.count() < c.count():
            return Shift.objects.get(shift_name="B")
        else:
            return Shift.objects.get(shift_name="C")


class Level(models.Model):
    level_number = models.FloatField()
    level_description = models.CharField(max_length=50)
    max_leaves = models.IntegerField(null=True)
    base_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return str(self.level_number) + " : " + self.level_description


class Qualification(models.Model):
    q_name = models.CharField(max_length=20)
    q_abbr = models.CharField(max_length=8)
    q_description = models.CharField(max_length=50)

    def __str__(self):
        return self.q_name + " (" + self.q_abbr + ")"


class Gender(models.Model):
    gender_name = models.CharField(max_length=15)

    def __str__(self):
        return self.gender_name


class AppUser(models.Model):
    app_user = models.OneToOneField(User, on_delete=models.CASCADE)
    age = models.IntegerField(null = True, default=None)
    address = models.ForeignKey(Address, null=True, on_delete=models.SET_NULL)
    photo = models.FileField(
        upload_to="staff/profile_pictures", default="default/staff_profile.png"
    )
    staff_gender = models.ForeignKey(Gender, null=True, on_delete=models.SET_NULL)
    department = models.ForeignKey(Department, null=True, on_delete=models.SET_NULL)
    pro_level = models.ForeignKey(Level, null=True, on_delete=models.SET_NULL)
    qualifications = models.ManyToManyField(Qualification)
    phone = models.IntegerField()
    lockdown = models.BooleanField(default=False)
    shift = models.ForeignKey(Shift, null=True, on_delete=models.SET_NULL, blank=True)
    registration_date = models.DateTimeField(auto_now_add=True, blank=True)
    occupabili = models.BooleanField(default=True)

    def __str__(self):
        if self.pro_level.level_number < 4:
                    return "{0} [{1}]".format(
                self.app_user.username, self.pro_level.level_description
                )

        return "{0} [department : {1} {2}]".format(
            self.app_user.username, self.department, self.pro_level.level_description
        )

    def is_manager(self):
        return DepartmentManager.objects.filter(
            manager=self, department=self.department
        )

    def check_profession(self, level_no):
        return self.pro_level.level_number == level_no

    def check_department(self, department_name):
        return self.department.department_name == department_name

    def is_shift(self):
        a = self.shift.start_time
        b = self.shift.end_time
        c = datetime.now().time()

        if b == time(0):
            return a < c
        else:
            return a < c < b

    def present(self):
        if self.is_shift() and self.occupabili:
            if (
                Attendance.objects.select_related("staff__department")
                .filter(
                    staff__department=self.department,
                    time_of_attendance__date=datetime.today(),
                )
                .count()
                < 1
            ):
                Attendance.register_all(self.department, self.shift)

            self.leaveapplications_set.filter(date__date=datetime.today()).update(
                canceled=True
            )
            at = Attendance.objects.get_or_create(
                time_of_attendance__date=datetime.today(), staff=self
            )[0]
            at.present = True
            at.save()
            return True
        else:
            return False


    def shift_complete(self):
        attendance_record = self.attendance_set.filter(
            time_of_attendance__date=datetime.today(), present=True
        ).update(time_of_leave=datetime.now())

    def days_absent_year(self):
        year = datetime.today().year

    def lock_now(self):
        self.lockdown = True
        self.save
        return True

    def get_notifications(self, flag):
        surgery_due = self.surgery_set.filter(
            models.Q(date_of_surgery=datetime.today())
            | models.Q(date_of_surgery=datetime.today() + timedelta(days=1)),
            end_time=None,
        )
        if flag:
            unread_messages = self.department.emessage_set.filter(
                personal=False,
                sent_time__gt=datetime.today() - timedelta(days=1),
            )
            announcements = self.department.announcement_set.filter(
                time_of_announcement__date__gt=(datetime.today() - timedelta(days=1))
            )
            return {
                "unread_messages": unread_messages,
                "announcements": announcements,
                "surgery_due": surgery_due,
            }

        else:
            unread_messages = self.emessage_set.filter(read_time=None, personal=True)
            return {"unread_messages": unread_messages, "surgery_due": surgery_due}

    def profession(self):
        profs = [
            "",
            "",
            "exicutive officer",
            "managerial staff",
            "doctor",
            "nurses",
            "non nursing staff",
            "non expertise staff",
        ]
        return profs[self.pro_level]

    def fine(self):
        fine_amnt = self.disciplinaryaction_set.filter(issued_date__month = datetime.today().month, fine__gt = 0).aggregate(Sum("fine"))["fine__sum"]
        if not fine_amnt:
            fine_amnt = 0
        return fine_amnt


class DepartmentManager(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    manager = models.ForeignKey(AppUser, null=True, on_delete=models.SET_NULL)

    def save(self, *args, **kwargs):
        if self.department == self.manager.department:
            super(DepartmentManager, self).save(*args, **kwargs)
        else:
            raise Http404

    def __str__(self):
        return self.manager.app_user.username


class Certificate(models.Model):
    def user_directory_path(instance, filename):
        ext = filename.split(".")[-1]
        new_name = instance.certificate_title + "." + ext
        return "/HospitalManagementSystem/media/HospitalManagementSystem/staff/{0}/{1}".format(
            instance.staff.app_user.username, new_name
        )

    staff = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    certificate_title = models.CharField(max_length=30, blank=True)
    photo = models.FileField(upload_to="staff/certificates", blank=True)

    class Meta:
        unique_together = (
            "staff",
            "certificate_title",
        )

    def __str__(self):
        return self.photo.name + " : " + str(self.staff)


class Accident(models.Model):
    type_name = models.CharField(max_length=40)

    def __str__(self):
        return self.type_name


class Announcement(models.Model):
    from_u = models.ForeignKey(
        AppUser, null=True, default=None, on_delete=models.SET_NULL
    )
    title = models.CharField(max_length=30)
    text = models.TextField(max_length=200)
    target_department = models.ManyToManyField(Department)
    time_of_announcement = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.from_u:
            return "{0} ,announced by {1}".format(self.title, self.from_u)
        else:
            return self.title + " : from  Administration"


class Fee(models.Model):
    item = models.CharField(max_length=15)
    amount = models.IntegerField(default=0)

    def __str__(self):
        return self.item + "- Rs." + str(self.amount)


class Salary(models.Model):
    staff = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    exp_increment = models.DecimalField("experience increment", max_digits=10, decimal_places=2, default=0)
    other_increment = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return "{0} : Rs.{1} ".format(self.staff.app_user, self.total_salary())

    def total_salary(self):
        return (
            self.staff.pro_level.base_salary
            + self.bonus
            + self.exp_increment
            + self.other_increment
            - self.staff.fine()
        )


class Attendance(models.Model):
    staff = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    present = models.BooleanField(default=False)
    time_of_attendance = models.DateTimeField(auto_now_add=True)
    time_of_leave = models.DateTimeField(null=True, default=None)

    def __str__(self):
        return "{0} is {1} on {2}".format(
            self.staff.app_user,
            (
                "present [recorded at {0}] ".format(self.time_of_attendance.time())
                if self.present
                else "absent"
            ),
            self.time_of_attendance.date(),
        )

    def register_all(department, shift):
        appusers = department.appuser_set.filter(shift=shift)
        for au in appusers:
            Attendance.objects.get_or_create(
                time_of_attendance__date=datetime.today(), staff=au, present=False
            )


class PatientPersonalReccord(models.Model):
    p_Fname = models.CharField(max_length=20)
    p_Lname = models.CharField(max_length=20)
    p_address = models.ForeignKey(Address, null=True, on_delete=models.SET_NULL)
    p_age = models.IntegerField()
    p_gender = models.ForeignKey(Gender, null=True, on_delete=models.SET_NULL)
    phone = models.IntegerField()
    created_date = models.DateTimeField(auto_now_add=True, blank=True)
    last_visited_date = models.DateTimeField(null=True)
    next_meeting_date = models.DateTimeField(null=True)
    photo = models.FileField(
        "photo/identity File", null=True, upload_to="patients", blank=True
    )
    active = models.BooleanField(default=False)
    deceased = models.BooleanField(default=False)

    def __str__(self):
        return "Number : {0}, {1} {2}".format(self.id, self.p_Fname, self.p_Lname)

    def get_active_health_reccord(self):
        try:
            hr = self.patienthealthreccord_set.get(status_code__lt=6)
            return hr
        except:
            return False

    def get_active_health_reccord_or_last(self):
        hr = self.patienthealthreccord_set.filter(status_code__lt=6)
        if not hr:
            hr = self.patienthealthreccord_set.all()
            if hr:
                hr = hr[0]
        else:
            hr = hr[0]
        return hr

    def get_active_bill(self):
        hr = self.get_active_health_reccord()
        if hr:
            return hr.bill_set.get(concluded=True)
        else:
            return False

    def mark_deceased(self):
        hr = self.get_active_health_reccord()


class PatientUnknown(models.Model):
    patient_identity_marks = models.CharField(max_length=250 * 2, null=True, blank=True)
    patient_gentder = models.ForeignKey(Gender, null=True, on_delete=models.SET_NULL)
    estimated_age = models.IntegerField(null=True)
    other_known_informations = models.CharField(
        max_length=250 * 2, null=True, blank=True
    )
    photo = models.FileField(
        "identity document", upload_to="unknown", null=True, blank=True
    )
    deceased = models.BooleanField(default=False)

    def __str__(self):
        return "U{3} : Aged {0} gender : {1}, with {2}".format(
            self.estimated_age, self.patient_gentder, self.patient_identity_marks, self.id
        )

    def get_active_health_reccord(self):
        hr = self.patienthealthreccord
        if hr.status_code < 6:
            return hr
        else:
            return False


class CauseOfDisease(models.Model):
    cause_name = models.CharField(max_length=50)
    cause_description = models.TextField(max_length=200)

    def __str__(self):
        return self.cause_name


class DiseaseType(models.Model):
    type_name = models.CharField(max_length=30)
    type_description = models.TextField(max_length=300)

    def __str__(self):
        return self.type_name


class Disease(models.Model):
    disease_name = models.CharField(max_length=50)
    remarks = models.CharField(max_length=200 * 2)
    affected_organs = models.ManyToManyField(HumanOrgan, blank = True)
    causes = models.ManyToManyField(CauseOfDisease, blank = True)
    known_medicines = models.ManyToManyField("Medicine", blank=True)
    disease_type = models.ForeignKey(DiseaseType, null = True, on_delete=models.SET_NULL)
    fatality_rate = models.DecimalField(default=0.00, max_digits=6, decimal_places=3)

    def __str__(self):
        return "{0} - {1} - Total Cases : {2}".format(
            self.pk, self.disease_name, self.patienthealthreccord_set.count()
        )
    
    def get_all_cases(self, year, month = None):
        if month:
            diceased = self.fatality_set.filter(date_of__year = year, date_of__month = month)
            patients_excluding_deceased = self.patienthealthreccord_set.filter(op_time_stamp__year=year, op_time_stamp__month = month).exclude(id__in = [d.hr.id for d in diceased])
        else:
            diceased = self.fatality_set.filter(date_of__year = year)
            patients_excluding_deceased = self.patienthealthreccord_set.filter(op_time_stamp__year=year).exclude(id__in = [d.hr.id for d in diceased])
        return (patients_excluding_deceased.count() + diceased.count())

    def get_deaths_at_hospital_info(self, year, month = None):
        if month:
            divisor = self.patienthealthreccord_set.filter(op_time_stamp__year=year, op_time_stamp__month=month)
            diseased_in_treatment = self.fatality_set.filter(date_of__year = year, hr__in = divisor, date_of__month = month)
        else:
            divisor = self.patienthealthreccord_set.filter(op_time_stamp__year=year)
            diseased_in_treatment = self.fatality_set.filter(date_of__year = year, hr__in = divisor)

        if divisor.count() == 0:
            return (0, 0)
        return (diseased_in_treatment.count(), divisor.count())

def all_diceases(years, diseases):
    total_diseases = []
    count_list = [[0, 0, 0, 0, 0] for i in range(diseases.count())]
    for year in years:
        temp_list = []
        for disease in diseases:
            deaths_and_cases = disease.get_deaths_at_hospital_info(year)
            temp_list.append(
                [
                    deaths_and_cases[1],
                    deaths_and_cases[0],
                    (0 if deaths_and_cases[1] == 0 else deaths_and_cases[0]/deaths_and_cases[1] * 100),
                    deaths_and_cases[0],
                    deaths_and_cases[1]
                ]
            )
        total_diseases.append(temp_list)
        count_list = [list(map(sum, zip(count_list[i], temp_list[i]))) for i in range(len(count_list))]

    return (total_diseases, count_list)

def all_diceases_year(year, diseases):
    total_diseases = []
    count_list = [[0, 0, 0, 0, 0] for i in range(diseases.count())]
    for month in range(1,13):
        temp_list = []
        for disease in diseases:
            deaths_and_cases = disease.get_deaths_at_hospital_info(year, month)
            temp_list.append(
                [
                    deaths_and_cases[1],
                    deaths_and_cases[0]
                ]
            )
        total_diseases.append(temp_list)
        count_list = [list(map(sum, zip(count_list[i], temp_list[i]))) for i in range(len(count_list))]

    for i in range(diseases.count()):
        deaths_and_cases = diseases[i].get_deaths_at_hospital_info(year)
        count_list[i].append(0 if deaths_and_cases[1] == 0 else deaths_and_cases[0]/deaths_and_cases[1] * 100)

    return (total_diseases, count_list)


class PatientHealthReccord(models.Model):
    patient = models.ForeignKey(
        PatientPersonalReccord, null=True, on_delete=models.SET_NULL
    )
    patient_unknown = models.OneToOneField(
        PatientUnknown, null=True, default=None, on_delete=models.SET_NULL
    )
    diseases = models.ManyToManyField(Disease, blank=True)
    companion_name = models.CharField(
        "companion name", max_length=30, null=True, blank=True
    )
    companion_phone = models.IntegerField(
        "companion phone", null=True, blank=True
    )
    departments = models.ManyToManyField(
        Department, blank=True
    )
    departments_visited = models.ManyToManyField(
        Department, blank=True, related_name= "visited_patients"
    )
    status_code = models.IntegerField(default=0)
    created_date = models.DateTimeField(auto_now_add=True, blank=True)
    modified_date = models.DateTimeField(auto_now=True, blank=True)
    op_time_stamp = models.DateTimeField(null=True)
#    op_time_stamp_change = models.IntegerField(default=0)
    accident = models.ForeignKey(
        Accident, null=True, on_delete=models.SET_NULL, default=None, blank = True
    )

    def __str__(self):
        departments = ",".join([dep.department_name for dep in self.departments.all()])
        if self.patient:
            return (
                "{0} - {1} - {2}".format(self.patient, departments, self.status())
            )
        else:
            return "Unknown Patient - {0} : [{1}]".format(
                self.patient_unknown, departments
            )

    def merge(self, hrs):
        hrs = hrs.exclude(id = self.id)
        for hr in hrs:
            hr.testresults_set.update(record = self)
            hr.surgery_set.update(record = self)
            hr.prescrption_set.update(record = self)
            hr.fatality_set.update(hr = hr)
            hr.patienttransfer_set.update(record = self)
            hr.admission_set.update(record = self)
            

    def get_bill(self):
        a = self.bill_set.all()
        return a.get(concluded=False)

    def save(self, patient=None, *args, **kwargs):
        super(PatientHealthReccord, self).save(*args, **kwargs)

        try:
            bill = self.get_bill()
        except Bill.DoesNotExist:
            Bill(record=self).save()

    def status(self):
        statuses = [
            "waiting",
            "consulted",
            "admitted but not cosulted",
            "consulted and admitted",
            "In Casuality",
            "checked out from room",
            "left hospital",
            "deceased"
        ]
        return statuses[self.status_code]

    def re_issue(self):
        PatientHealthReccord.objects.filter(status_code=0).update(status_code=5)
        self.status_code = 0
        self.op_time_stamp = datetime.now(timezone.utc)
        self.modified_date = datetime.now(timezone.utc)
        self.patient.next_meeting_date = None
        self.patient.save()
        self.save()
        self.bill_set.filter(concluded=False).update(concluded=True)
        Bill(record=self).save()
        return self

    def dismiss(self):
        if not self.admission_status() or self.admission_status() == 3:
            self.status_code = 6
            self.save()
            self.bill_set.filter(concluded=False).update(concluded=True)

    def discharge(self, adm):
        bill = self.get_bill()
        self.status_code = 5
        self.save()
        if adm:
            self.check_out(adm)

    def check_out(self, adm):
        adm.room.vacant_beds += 1
        adm.room.save()
        adm.dis_time = datetime.now(timezone.utc)
        adm.save()
        bill = self.get_bill()
        bill.room += Decimal(adm.total_rent())
        bill.save()

    def admit(self, obj):
        room = obj.room
        a = self.admission_status()
        if room.vacant_beds > 0 and self.admission_status() != 0:
            obj.ad_time = datetime.now(timezone.utc)
            obj.save()
            if self.status_code < 2:
                self.status_code += 2
                self.save()

            obj.room.vacant_beds -= 1
            obj.room.save()
            return True
        else:
            return False

    def admission_status(self):
        if self.admission_set.filter(ad_time=None):
            return 1  # patient is admitted but not checked into any room

        elif self.admission_set.exclude(ad_time=None).filter(dis_time=None):
            return 2  # Patient is admitted and has checked in

        elif self.admission_set.exclude(ad_time=None).exclude(dis_time=None):
            return 3  # Patient has checked out

        else:
            return 0  # patient is not admitted

    def leave(self):
        bill = self.get_bill()
        if bill.payment_complete():
            self.status_code = 6
            self.save()
            if self.patient:
                self.patient.active = False
                self.patient.save()
        else:
            return False

    def get_room(self):
        status = self.admission_status()
        if status == 1:
            return ", is awaiting admission"
        elif status == 2:
            return ", is admitted @ {0}".format(
                str(
                    self.admission_set.exclude(ad_time=None)
                    .filter(dis_time=None)[0]
                    .room
                )
            )
        elif status == 3:
            return ", was admitted @ {0}, but now discharged".format(
                str(
                    self.admission_set.exclude(ad_time=None)
                    .exclude(dis_time=None)[0]
                    .room
                )
            )
        else:
            return ", is not admitted"

    def tests(self):
        return Test.objects.filter(
            id__in=[tr.test.id for tr in self.testresults_set.all()]
        )


class PatientAssociatedFiles(models.Model):
    record = models.ForeignKey(
        PatientHealthReccord, null=True, on_delete=models.CASCADE
    )
    title = models.CharField("what is this photo? ", max_length=25, blank=True, default="untitled")
    photo = models.FileField(
        "Document File", null=True, upload_to="patients", blank=True
    )

    def __str__(self):
        return "{0} - File : {1}".format(self.record, self.title)


class HealthRemarks(models.Model):
    record = models.ForeignKey(
        PatientHealthReccord, null=True, on_delete=models.SET_NULL
    )
    rem_text = models.TextField(blank=True)
    remark_by = models.ForeignKey(AppUser, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.rem_text + " --  remarked by Dr. " + str(self.remark_by)


class Medicine(models.Model):
    medicine_name = models.CharField(max_length=20)
    amnt_for_one = models.DecimalField(max_digits=10, decimal_places=2)
    stock_now = models.IntegerField(null=True)
    last_refill_date = models.DateTimeField(null=True)

    def __str__(self):
        return (
            self.medicine_name
            + " - Rs."
            + str(self.amnt_for_one)
            + ", stock: "
            + str(self.stock_now)
        )

    def reduce_stock(self, number):
        if self.is_available(number):
            self.stock_now -= number
            self.save()
            return True
        else:
            return False

    def is_available(self, number):
        return self.stock_now >= number


class Prescription(models.Model):
    record = models.ForeignKey(
        PatientHealthReccord, null=True, on_delete=models.SET_NULL
    )
    medicine = models.ForeignKey(Medicine, null=True, on_delete=models.SET_NULL)
    med_number = models.IntegerField(
        "Total days", null=True
    )  # number of days of consumption
    med_freq = models.IntegerField(null=True)  # number of takings a day
    is_given = models.BooleanField(default=False)
    given_date = models.DateTimeField(null=True)
    canceled = models.BooleanField(default=False)
    pres_by = models.ForeignKey(AppUser, null = True, on_delete=models.SET_NULL)

    def __str__(self):
        if self.medicine:
            return (
                self.medicine.medicine_name
                + " - "
                + str(self.med_number)
                + " days ( "
                + str(self.med_freq)
                + " per day )"
            )
        else:
            return ""

    def taking(self):
        return "{0} / day for {1} days".format(self.med_freq, self.med_number)

    def available(self):
        return self.medicine.stock_now

    def total_amnt(self):
        return (
            Decimal(self.med_number)
            * Decimal(self.med_freq)
            * self.medicine.amnt_for_one
        )

    def add_to_bill(self):
        bill = self.record.get_bill()
        bill.medicines += self.total_amnt()
        bill.save()
        self.is_given = True
        self.given_date = datetime.today()
        self.save()

    def deduct_from_bill(self):  # call it on_deletion of prescrption
        bill = self.record.get_bill()
        bill.medicines -= self.total_amnt()
        bill.save()

    def alter_amnt(self, old_amnt, new_amnt):
        amount = old_amnt - new_amnt
        bill = self.record.get_bill()
        bill.medicines -= amount
        bill.save()


def all_medications(years, med=None):
    medications = []
    count = 0
    if med:
        for year in years:
            avl_meds = Prescription.objects.filter(medicine=med, given_date__year=year)
            if avl_meds:
                meds_total = avl_meds.annotate(
                    total=F("med_number") * F("med_freq")
                ).aggregate(Sum("total"))["total__sum"]
                medications.append(
                    (
                        year,
                        "{1} nos for {0} patients".format(avl_meds.count(), meds_total),
                    )
                )
                if meds_total:
                    count += meds_total

    else:
        for year in years:
            avl_meds = Prescription.objects.filter(given_date__year=year)
            if avl_meds:
                meds_total = avl_meds.annotate(
                    total=F("med_number") * F("med_freq")
                ).aggregate(Sum("total"))["total__sum"]
                medications.append(
                    (
                        year,
                        "{1} nos for {0} patients".format(avl_meds.count(), meds_total),
                    )
                )
                if meds_total:
                    count += meds_total

    return (medications, count)


def all_medications_current_year(med=None):
    medications = []
    count = 0
    if med:
        avl_meds = Prescription.objects.filter(
            medicine=med, given_date__year=datetime.today().year
        )
    else:
        avl_meds = Prescription.objects.filter(given_date__year=datetime.today().year)

    if avl_meds:
        for mon in range(1, 13):
            mnth_meds = avl_meds.filter(given_date__month=mon)

            meds_total = mnth_meds.annotate(
                total=F("med_number") * F("med_freq")
            ).aggregate(Sum("total"))["total__sum"]
            medications.append(
                (
                    calendar.month_name[mon],
                    "{1} nos for {0} patients".format(mnth_meds.count(), meds_total),
                )
            )
            if meds_total:
                count += meds_total

    return (medications, count)


class Test(models.Model):
    test_name = models.CharField(max_length=30)
    test_abbr = models.CharField(max_length=30)
    test_description = models.CharField(max_length=100)
    test_amnt = models.IntegerField()

    def __str__(self):
        return "{0} {1} {2}".format(self.test_name, self.test_abbr, self.test_amnt)


class TestResults(models.Model):
    record = models.ForeignKey(
        PatientHealthReccord, null=True, on_delete=models.SET_NULL
    )
    test = models.ForeignKey(Test, null=True, on_delete=models.SET_NULL)
    remarks = models.CharField(max_length=250, null=True)
    time_ordered = models.DateTimeField(auto_now_add=True, blank=True)
    time_taken = models.DateTimeField(null=True)
    issued_by = models.ForeignKey(AppUser, null = True, on_delete=models.SET_NULL)

    def __str__(self):
        return "{0} - {1} (taken @ {2})".format(self.test.test_name, self.record, self.time_taken)

    def patient(self):
        return str(self.record.patient)

    def add_to_bill(self):
        bill = self.record.get_bill()
        bill.tests += self.test.test_amnt
        bill.save()

    def deduct_from_bill(self):
        bill = self.record.get_bill()
        bill.tests -= self.test.test_amnt
        bill.save()

    def alter_amnt(self, old_amnt, new_amnt):
        amount = old_amnt - new_amnt
        bill = self.record.get_bill()
        bill.tests -= amount
        bill.save()

    def stamp_time(self):
        if not self.time_taken:
            self.time_taken = datetime.now()
            self.save()


def all_tests(years, test=None):
    tests = []
    count = 0
    if test:
        for year in years:
            avl_tests = TestResults.objects.filter(test=test, time_taken__year=year)
            if avl_tests:
                tests.append((year, avl_tests.count()))
                count += avl_tests.count()

    else:
        for year in years:
            avl_tests = TestResults.objects.filter(time_taken__year=year)
            if avl_tests:
                tests.append((year, avl_tests.count()))
                count += avl_tests.count()

    return (tests, count)


def all_tests_current_year(test=None):
    tests = []
    count = 0
    if test:
        avl_tests = TestResults.objects.filter(
            test=test, time_taken__year=datetime.today().year
        )
    else:
        avl_tests = TestResults.objects.filter(time_taken__year=datetime.today().year)

    if avl_tests:
        for mon in range(1, 13):
            mnth_tests = avl_tests.filter(time_taken__month=mon)
            tests.append((calendar.month_name[mon], mnth_tests.count()))

    count = avl_tests.count()

    return (tests, count)


class TRDocuments(models.Model):
    tr = models.ForeignKey(TestResults, on_delete=models.CASCADE)
    title = models.CharField(max_length=30, null=True, default="No title", blank=True)
    photo = models.FileField(
        "Document File", null=True, upload_to="patients", blank=True
    )

    def __str__(self):
        return "Uploaded document of " + str(self.tr)


class RoomType(models.Model):
    type_name = models.CharField(max_length=10)
    daily_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_beds = models.IntegerField()

    def __str__(self):
        return "{0} (Maximum beds - {1}) - Rs.{2} daily".format(
            self.type_name, self.max_beds, str(self.daily_charge)
        )


class Room(models.Model):
    room_no = models.CharField(max_length=5, unique=True)
    roomtype = models.ForeignKey(RoomType, null=True, on_delete=models.SET_NULL)
    vacant_beds = models.IntegerField()

    def __str__(self):
        return "Room - {0},  vacant beds - {1}, [{2}]".format(
            self.room_no, self.vacant_beds, self.roomtype
        )

    def is_full(self):
        return self.vacant_beds < 1


class Admission(models.Model):
    record = models.ForeignKey(
        PatientHealthReccord, null=True, on_delete=models.CASCADE
    )
    room = models.ForeignKey(Room, null=True, on_delete=models.SET_NULL)
    ad_time = models.DateTimeField(null=True)
    dis_time = models.DateTimeField(null=True)

    def __str__(self):
        if self.ad_time:
            return "{0} ,   Room: {1}   [amount so far : Rs.{2}]".format(
                self.record.patient if self.record.patient else self.record, self.room.room_no, self.total_rent()
            )
        else:
            return "{0} is waiting Admission".format(
                self.record.patient if self.record.patient else self.record
            )

    def total_rent(self):
        if self.dis_time:
            diff = self.dis_time - self.ad_time
        else:
            diff = datetime.now(timezone.utc) - self.ad_time

        hrs = diff.seconds / 60 / 60
        days = diff.days + 1 if hrs > 1 else diff.days
        return days * self.room.roomtype.daily_charge


def all_admissions(years, rtype=None):
    admissions = []
    count = 0
    if rtype:
        for year in years:
            avl_admissions = Admission.objects.select_related("room__roomtype").filter(
                room__roomtype=rtype, ad_time__year=year
            )
            if avl_admissions:
                admissions.append((year, avl_admissions.count()))
                count += avl_admissions.count()

    else:
        for year in years:
            avl_admissions = Admission.objects.filter(ad_time__year=year)
            if avl_admissions:
                admissions.append((year, avl_admissions.count()))
                count += avl_admissions.count()

    return (admissions, count)


def all_admissions_current_year(rtype=None):
    admissions = []
    count = 0
    if rtype:
        avl_admissions = Admission.objects.select_related("room__roomtype").filter(
            room__roomtype=rtype, ad_time__year=datetime.today().year
        )
    else:
        avl_admissions = Admission.objects.filter(ad_time__year=datetime.today().year)

    if avl_admissions:
        for mon in range(1, 13):
            mnth_admissions = avl_admissions.filter(ad_time__month=mon)
            admissions.append((calendar.month_name[mon], mnth_admissions.count()))

    count = avl_admissions.count()

    return (admissions, count)


class Surgery(models.Model):
    record = models.ForeignKey(
        PatientHealthReccord, null=True, on_delete=models.SET_NULL
    )
    surgery_name = models.CharField(max_length=30, default="Unspecified")
    organ_under_surgery = models.ForeignKey(HumanOrgan, null = True, on_delete=models.SET_NULL, blank = True)
    reason = models.CharField(max_length=20, default="Unspecified")
    initiated_by = models.ForeignKey(AppUser, null = True, on_delete=models.SET_NULL, related_name="surgeries_initiated") 
    team = models.ManyToManyField(AppUser, blank=True)
    team.help_text = "team leader must be chosen"
    team_leader = models.ForeignKey(AppUser, null = True, on_delete=models.SET_NULL, blank=True, related_name="surgeries_led")
    theatre = models.CharField(max_length=20, default="Unspecified")
    total_amnt = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    prepay_amnt = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_prepaid = models.BooleanField("Prepayment made", default=False)
    date_of_surgery = models.DateField(null=True)
    start_time = models.TimeField("start time (you can change it later)", null=True)
    end_date = models.DateField(null=True, blank=True)
    end_time = models.TimeField(null=True)
    patient_report_time = models.TimeField(null=True, blank=True)
    team_report_time = models.TimeField(null=True, blank=True)
    surgery_report = models.TextField(
        "report", max_length=200 * 2, default="Surgery not over"
    )
    is_autopsy = models.BooleanField(default=False)

    def __str__(self):
        if self.record.patient_unknown:
            return "{0} for {1}".format(self.surgery_name, self.record)
        else:
            return "{0} for {1}".format(self.surgery_name, self.record.patient)

    def save(self, *args, **kwargs):
        super(Surgery, self).save(*args, **kwargs)

    def add_to_bill(self):
        bill = self.record.get_bill()
        bill.surgeries += self.total_amnt
        bill.save()

    def deduct_from_bill(self):
        bill = self.record.get_bill()
        bill.surgeries -= self.total_amnt
        bill.save()

    def alter_amnt(self, old_amnt, new_amnt):
        amount = old_amnt - new_amnt
        bill = self.record.get_bill()
        bill.surgeries -= amount
        bill.save()

    def prepay(self):
        if not self.is_prepaid:
            self.is_prepaid = True
            self.save()
            bill = self.record.get_bill()
            bill.total_payed += self.prepay_amnt
            bill.save()


class SurgeryDocuments(models.Model):
    surgery = models.ForeignKey(Surgery, on_delete=models.CASCADE)
    title = models.CharField("what is this photo? ", max_length=25, blank=True)
    photo = models.FileField(
        "Document File", null=True, upload_to="patients", blank=True
    )

    def __str__(self):
        return self.title + " document of " + str(self.surgery)


class PatientTransfer(models.Model):
    record = models.ForeignKey(
        PatientHealthReccord, null=True, on_delete=models.SET_NULL
    )
    outwrad = models.BooleanField(
        "Transferring to another hospital (No, if transferring is to this hospital)",
        null=True,
        default=None,
    )
    transfer_time = models.DateTimeField("Date and time of transfer", null=True)
    remarks = models.TextField(max_length=150 * 2)

    def __str__(self):
        if self.outwrad:
            return "{0} transferred from this hospital @ {1} : around {2}".format((self.record.patient if self.record.patient else self.record.patient_unknown), self.transfer_time.date(), self.transfer_time.hour)
        else:
            return "{0} transferred to this hospital @ {1} : around {2}".format((self.record.patient if self.record.patient else self.record.patient_unknown), self.transfer_time.date(),self.transfer_time.hour)


class Bill(models.Model):
    record = models.ForeignKey(PatientHealthReccord, on_delete=models.CASCADE)
    medicines = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tests = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    surgeries = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    room = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    consult_and_ticket_fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_time = models.DateTimeField(null = True, auto_now = True)
    concluded = models.BooleanField(default=False)
    total_payed = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amt_so_far = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    def __str__(self):
        return str(self.record) + " - " + str(self.total_amt_so_far)

    def pay(self, amount):
        if self.total_amt_so_far - self.total_payed - self.deductions < amount:
            return "Check amount"
        else:
            self.total_payed += amount
            self.save()

    def refresh_bill(self):
        self.total_amt_so_far = (
            self.medicines
            + self.tests
            + self.surgeries
            + self.room
            + self.consult_and_ticket_fee
        )
        self.save()

    def charge_for_consulting(self):
        self.refresh_bill()
        try:
            if self.consult_and_ticket_fee:
                return

            elif not self.record.patient:
                self.consult_and_ticket_fee = Fee.objects.get(item="New ticket").amount
                self.save()

            elif self.record.patient.created_date > (
                datetime.now(timezone.utc) - timedelta(days=1)
            ):
                self.consult_and_ticket_fee = Fee.objects.get(item="New ticket").amount
                self.save()

            else:
                self.consult_and_ticket_fee = Fee.objects.get(item="Consulting").amount
                self.save()
        except:
            return

    def payment_complete(self):
        return self.total_amt_so_far - self.deductions == self.total_payed


class LeaveApplications(models.Model):
    date = models.DateTimeField()
    applicant = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    approved = models.BooleanField(null=True, default=None)
    reason = models.TextField(
        "why do you do this?", max_length=250 * 2, default="Unspecified"
    )
    canceled = models.BooleanField("cancel", null=True, default=None)

    def __str__(self):
        return "{0} - {1} : status - {2} {3}".format(
            self.applicant,
            self.date.date(),
            self.status(),
            ("but canceled" if self.canceled else ""),
        )

    def status(self):
        return (
            "Approved"
            if self.approved
            else ("Pending" if self.approved == None else "Disapproved")
        )

    def approval_possible(self):
        nav = datetime.now()
        if (nav.date() < self.date.date() or
            ((nav.date() == self.date.date())
            and (
                nav.time() < self.applicant.shift.start_time
            ))):
            return True
        return False


class StaffReport(models.Model):
    Staff = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    remark = models.TextField(max_length=200 * 4)
    remark_by = models.ForeignKey(
        AppUser, null=True, on_delete=models.SET_NULL, related_name="remarks_made"
    )
    stop_editing = models.BooleanField(
        "stop editing of this report", null=True, default=False
    )
    filed_date = models.DateField(auto_now_add=True, null=True)
    dismissed = models.BooleanField(
        "report reviewed", null=True, default=False
    )

    def __str__(self):
        return "report on {0}, filed @ {1}".format(self.Staff, self.filed_date)


class ComplaintsFeedback(models.Model):
    is_compaint = models.BooleanField(default=False)
    sender = models.ForeignKey(AppUser, null=True, on_delete=models.SET_NULL)
    on_behalf = models.ForeignKey(
        PatientPersonalReccord, null=True, on_delete=models.SET_NULL
    )
    concerned_department = models.ForeignKey(
        Department, null=True, on_delete=models.SET_NULL
    )
    subject = models.CharField(max_length=30, null=True, blank=True)
    concerned_staff = models.ForeignKey(
        AppUser,
        null=True,
        on_delete=models.SET_NULL,
        related_name="complaints_concerned",
        blank=True,
    )
    text = models.TextField("Complaint", max_length=200)
    time_filed = models.DateTimeField(auto_now_add=True)
    authority_remark = models.TextField(null=True, max_length=200)
    concluded = models.BooleanField(null=True, default=False)

    def __str__(self):
        if self.on_behalf:
            return "{0} : {1} - from {2} @{3} {4}".format(
                ("complaint" if self.is_compaint else "Feedback"),
                self.subject,
                self.on_behalf,
                self.time_filed.date(),
                "- concluded" if self.concluded else ""
            )
        else:
            return "{0} : {1} - from {2} @{3} {4}".format(
                ("complaint" if self.is_compaint else "Feedback"),
                self.subject,
                self.sender,
                self.time_filed.date(),
                "- concluded" if self.concluded else ""
            )


class DisciplinaryAction(models.Model):
    person = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    fine = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    start_date = models.DateTimeField(null=True)
    end_date = models.DateTimeField(null=True, blank=True)
    is_complete = models.BooleanField("mark as completed/ canceled", null=True, default=None)
    is_dismissal = models.BooleanField("dismissed", null=True, default=None)
    reason = models.TextField(max_length=300)
    issued_date = models.DateField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super(DisciplinaryAction, self).save(*args, **kwargs)

        self.refresh_from_db()
        if self.is_complete:
            self.person.occupabili = True
            self.person.save()
        else:
            self.person.occupabili = False
            self.person.save()

        self.refresh_from_db()
        if self.is_dismissal:
            self.person.department = None
            self.person.save()

    def __str__(self):
        return "{0}, {1} to {2}".format(
            self.person.app_user, self.start_date.date(), self.end_date
        )


class EMessage(models.Model):
    sender = models.ForeignKey(
        AppUser, null=True, on_delete=models.SET_NULL, related_name="sent_messages"
    )
    personal = models.BooleanField(default=True)
    reciever = models.ForeignKey(
        AppUser, null=True, on_delete=models.SET_NULL, verbose_name="To"
    )
    sender_dept = models.ForeignKey(
        Department, null=True, on_delete=models.SET_NULL, related_name="messages_from_dept"
    )
    reciever_dept = models.ForeignKey(
        Department, null=True, on_delete=models.SET_NULL, verbose_name="To"
    )
    subject = models.CharField(max_length=50, default="no subject")
    text = models.TextField()
    sent_time = models.DateTimeField(auto_now_add=True, blank=True)
    read_time = models.DateTimeField(null=True)

    def __str__(self):
        if self.personal:
            return (
                " From "
                + str(self.sender.app_user)
                + "  To "
                + str(self.reciever.app_user)
                + "  :  "
                + self.subject
            )
        else:
            return (
                " from "
                + str(self.sender_dept)
                + "  To "
                + str(self.reciever_dept)
                + "  :  "
                + self.subject
            )


class Inventory(models.Model):
    item = models.CharField(max_length=20)
    description = models.CharField(max_length=50)
    added_by = models.ForeignKey(AppUser, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.item


class DepartmentInventory(models.Model):
    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, related_name="owned_inventories"
    )
    item = models.ForeignKey(Inventory, on_delete=models.CASCADE)
    count = models.IntegerField()

    def __str__(self):
        return (
            str(self.count)
            + " "
            + str(self.item)
            + "s, "
            + str(self.department)
            + " department"
        )


class PurchaseList(models.Model):
    department = models.ForeignKey(
        Department, null=True, on_delete=models.SET_NULL, related_name="list_to_buy"
    )
    item = models.ForeignKey(Inventory, on_delete=models.CASCADE)
    requird_num = models.IntegerField("required number of items")
    item_gained = models.IntegerField(default=0)
    total_price = models.DecimalField(
        " total price (without discount)", max_digits=10, decimal_places=2, default=0
    )
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    posted_date = models.DateTimeField(auto_now_add=True, blank=True)
    aquired_date = models.DateTimeField(null = True, blank=True)
    closed = models.BooleanField("is this order closed?", null=True, default=None)

    def __str__(self):
        if self.closed:
            return "{0}  {1} for {2} department ordered on {4} [{3} gained] purchase date-{5}".format(
                self.requird_num,
                self.item,
                self.department,
                self.item_gained,
                self.posted_date.date(),
                self.aquired_date.date()
            )
        else:
            return "{0}  {1} for {2} department ordered on {4} [{3} gained]".format(
                self.requird_num,
                self.item,
                self.department,
                self.item_gained,
                self.posted_date.date(),
            )


def all_purchases(years, dep=None, inv=None):
    purchases = []
    count = 0
    if dep:
        for year in years:
            if inv:
                avl_purchases = dep.list_to_buy.filter(
                    aquired_date__year=year, item=inv
                )
            else:
                avl_purchases = dep.list_to_buy.filter(aquired_date__year=year)

            if avl_purchases:
                purchases.append((year, avl_purchases.count()))
                count += avl_purchases.count()

    else:
        for year in years:
            if inv:
                avl_purchases = PurchaseList.objects.filter(
                    aquired_date__year=year, item=inv
                )
            else:
                avl_purchases = PurchaseList.objects.filter(aquired_date__year=year)

            if avl_purchases:
                purchases.append((year, avl_purchases.count()))
                count += avl_purchases.count()

    return (purchases, count)


def all_purchases_current_year(dep=None, inv=None):
    purchases = []
    count = 0
    if dep:
        if inv:
            avl_purchases = dep.list_to_buy.filter(
                aquired_date__year=datetime.today().year, item=inv
            )
        else:
            avl_purchases = dep.list_to_buy.filter(
                aquired_date__year=datetime.today().year
            )

    else:
        if inv:
            avl_purchases = PurchaseList.objects.filter(
                aquired_date__year=datetime.today().year, item=inv
            )
        else:
            avl_purchases = PurchaseList.objects.filter(
                aquired_date__year=datetime.today().year, item=inv
            )

    if avl_purchases:
        for mon in range(1, 13):
            mnth_purchases = avl_purchases.filter(aquired_date__month=mon)
            purchases.append((calendar.month_name[mon], mnth_purchases.count()))

    count = avl_purchases.count()

    return (purchases, count)


class Fatality(models.Model):
    autopsy = models.ForeignKey(Surgery, null=True, on_delete=models.SET_NULL)
    hr = models.ForeignKey(PatientHealthReccord, on_delete=models.CASCADE)
    date_of = models.DateField("date of death", null=True, blank=True)
    time_of = models.TimeField("time of death", null=True, blank=True)
    cause = models.ForeignKey(Disease, null=True, on_delete=models.SET_NULL, blank=True)
    cause_description = models.TextField(null=True, blank=True)
    death_report = models.TextField(null=True, blank=True)
    updated_by = models.ForeignKey(AppUser, null = True, on_delete=models.SET_NULL)

    def __str__(self):
        if self.hr.patient_unknown:
            return "{0} died on {1} around {2}".format(
                self.hr.patient_unknown, self.date_of, self.time_of
            )
        else:
            return "{0} died on {1} around {2}".format(
                self.hr.patient, self.date_of, self.time_of
            )


class Morgue(models.Model):
    patient = models.ForeignKey(PatientPersonalReccord, on_delete=models.CASCADE)
    only_morgue_service = models.BooleanField(null=True, default=None)
    door_no = models.CharField(max_length=20)
    start_date = models.DateField(auto_now_add=True)
    start_time = models.TimeField(auto_now_add=True)
    end_date = models.DateField(null=True)
    end_time = models.TimeField(null=True)
    dismissed = models.BooleanField(null=True, default=None)
    amnt = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    def __str__(self):
        return "{0} at door {1}".format(self.patient, self.door_no)

def all_morgues(years):
    admissions = []
    count = 0
    for year in years:
        avl_mrg_admissions = Morgue.objects.filter(start_date__year=year)
        if avl_mrg_admissions:
            admissions.append((year, avl_mrg_admissions.count()))
            count += avl_mrg_admissions.count()

    return (admissions, count)


def morgues_year(year):
    admissions = []
    count = 0
    avl_mrg_admissions = Morgue.objects.filter(start_date__year=datetime.today().year)

    if avl_mrg_admissions:
        for mon in range(1, 13):
            mnth_admissions = avl_mrg_admissions.filter(start_date__month=mon)
            admissions.append((calendar.month_name[mon], mnth_admissions.count()))

    count = avl_mrg_admissions.count()

    return (admissions, count)