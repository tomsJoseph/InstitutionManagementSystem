from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.views import (
    PasswordChangeView,
    PasswordResetView,
    PasswordResetConfirmView,
)
from django.db.models import Sum, Count
from difflib import SequenceMatcher
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from datetime import datetime, time, timedelta
from django.forms.models import model_to_dict
from django.urls import reverse, reverse_lazy
from django.dispatch import receiver
from django.shortcuts import render
from django.views.generic import *
from .helpers import serialize_qs
import json as simplejson
from django import forms
from .models import *
from .forms import *


def department_active(appuser):
    if appuser.lockdown:
        return True
    else:
        return False


def activate_deartment(request):
    request.user.appuser.lock_now()
    return True


def only_medical_departments(user):
    if (
        user.is_authenticated
        and user.appuser.lockdown
        and user.appuser.department.is_medical
    ):
        return True
    else:
        return False


def only_medical(user):
    if (
        user.is_authenticated
        and user.appuser.department.is_medical
    ):
        return True
    else:
        return False

def surgery_info_control(user, surgery):
    if (
        user.is_authenticated
        and not user.appuser.lockdown
        and (user.appuser in surgery.team.all())
    ):
        return True
    else:
        return False


def surgery_key_control(user, surgery):
    if (
        user.is_authenticated
        and not user.appuser.lockdown
        and user.appuser.check_profession(4)
        and (((user.appuser == surgery.initiated_by or surgery.team_leader == user.appuser or user.appuser in surgery.team.all()) or (not surgery.team_leader)))
    ):
        return True
    else:
        return False


def only_department(user, department):
    if (
        user.is_authenticated
        and user.appuser.lockdown
        and user.appuser.check_department(department)
    ):
        return True
    else:
        return False


def only_departments(user, departments):
    if user.is_authenticated and user.appuser.lockdown:
        for department in departments:
            department = (
                department if type(department) == str else department.department_name
            )
            if user.appuser.check_department(department):
                return True
        return False
    else:
        return False


def only_above_prof(user, pro_level):
    if (
        user.is_authenticated
        and not user.appuser.lockdown
        and user.appuser.pro_level.level_number <= pro_level
    ):
        return True
    else:
        return False


def only_department_and_prof(user, department, pro_level):
    if (
        user.is_authenticated
        and user.appuser.lockdown
        and user.appuser.check_department(department)
        and user.appuser.check_profession(pro_level)
    ):
        return True
    else:
        return False


def only_above(user, level):
    if (
        user.is_authenticated
        and not user.appuser.lockdown
        and user.appuser.pro_level.level_number <= level
    ):
        return True
    else:
        return False


def only_doctors(user):
    if (
        user.is_authenticated
        and not user.appuser.lockdown
        and user.appuser.check_profession(4)
    ):
        return True
    else:
        return False


def only_managers(user):
    if (
        user.is_authenticated
        and bool(user.appuser.departmentmanager_set.all())
        and not user.appuser.lockdown
    ):
        return True
    else:
        return False


def only_doctors_and_departments(user, departments):
    if (
        user.is_authenticated
        and not user.appuser.lockdown
        and user.appuser.check_profession(4)
    ):
        for department in departments:
            if user.appuser.check_department(department):
                return True
        return False
    else:
        return False


def only_managers_of_department(user, department):
    if (
        user.is_authenticated
        and not user.appuser.lockdown
        and user.appuser.is_manager()
        and user.appuser.department == department
    ):
        return True
    else:
        return False


def possessing_department(user, the_class, pk):
    try:
        obj = the_class.objects.get(pk=pk)
        if obj.department == user.appuser.department:
            return True
        else:
            return False
    except:
        return False


def personal_message_possession(user, pk):
    try:
        obj = EMessage.objects.get(pk=pk)
        if obj.sender == user.appuser or obj.receiver == user.appuser:
            return True
        else:
            return False
    except:
        return False


def message_possession(user, pk):
    obj = EMessage.objects.get(pk=pk)
    if user.appuser.lockdown and not obj.personal:
        if (
            obj.sender_dept == user.appuser.department
            or obj.reciever_dept == user.appuser.department
        ):
            return True
        else:
            return False
    elif not user.appuser.lockdown and obj.personal:
        if (
            obj.sender == user.appuser
            or obj.reciever == user.appuser
        ):
            return True
        else:
            return False

    return False


def signup(request):
    if request.user.is_superuser or only_above(request.user, 3) or only_managers(request.user):
        if request.method == "POST":
            form = SignUpForm(request.POST)
            sub_form = UserFormForApp(request.POST, request.FILES)
            sub_form_addr = AddressForm(request.POST)

            if form.is_valid():
                form.save()
                username = form.cleaned_data.get("username")
                raw_password = form.cleaned_data.get("password1")
                user = authenticate(username=username, password=raw_password)
                login(request, user)

                if sub_form.is_valid():
                    qs = sub_form.cleaned_data.get("qualifications")
                    del sub_form.cleaned_data["qualifications"]
                    sub_form_addr.is_valid()
                    if sub_form_addr.is_valid():
                        ad = sub_form_addr.save(commit=False)
                        ad.save()

                        appuser = AppUser(**sub_form.cleaned_data)
                        appuser.app_user = user
                        appuser.address = ad
                        appuser.save()
                        appuser.qualifications.set(qs)
                        appuser.save()
                        Salary.objects.get_or_create(staff=appuser)

                    else:
                        user.delete()
                        raise PermissionDenied
                else:
                    user.delete()
                    raise PermissionDenied

                return redirect("SelectPage")

        else:
            form = SignUpForm()
            sub_form = UserFormForApp()
            sub_form_addr = AddressForm()

        data = {
            "form": form,
            "sub_form": sub_form,
            "sub_form_addr": sub_form_addr,
        }

        if not request.user.is_superuser:
            data["links"] = get_links(request.user.appuser)
            data["base_temp"] = "Hospital/EBase.html" if request.user.appuser.pro_level.level_number < 4 else "Hospital/SBase.html"
        else:
            data["base_temp"] = "Hospital/base.html"

        return render(request, "Hospital/signup.html", data,)
    else:
        return redirect("login")


def selection_page_admin(request):
    if request.user.is_superuser:
        return render(request, "Hospital/admin_select.html")
    else:
        return redirect("login")


def selection_page(request):
    if request.user.is_authenticated:
        au = request.user.appuser  # appuser
        context = {}
        if au.lockdown:
            logout(request)
        elif au.pro_level.level_number < 4:
            return redirect("M_ExecutiveHome")
        elif not request.user.appuser.department:
            return redirect("login")
        else:
            info = [au.department, request.user.username]
            context["info"] = info
        return render(request, "Hospital/SelectPage.html", context)
    else:
        return redirect("login")


def get_links(au):
    links = [("ListAnnouncements", "announcements")]
    if au.pro_level.level_number < 4:
        pass
    elif not au.lockdown:
        dep = au.department
        if dep.is_manager(au):
            links.extend(
                [
                    ("StaffAttendance", "Staff Attendance"),
                    ("StaffReportList", "Staff Reports"),
                    ("ListLeaves", "Leave Applications"),
                    ("AbsenteeReport", "Absentee Reports"),
                    ("AllStaffs", "Staffs"),
                ]
            )
            if au.check_department('OP'):
                links.append(('ChangeShift', 'Change Shift'))

        if au.check_profession(4):
            links.extend([("SearchPage", "Patient Consulting"), ("TheDeparted", "Departed"), ("SurgeryList", "surgeries")])

    else:
        dep = au.department
        if dep.department_name == "Transport":
            links.extend(
                [
                    ("TotalPurchaseList", "Purchase List"),
                    ("OldPurchaseList", "Old Purchase Orders"),
                ]
            )

        elif dep.department_name == "OP" or dep.department_name == "Casuality":
            links.extend(
                [
                    ("OPPage", "Patient Registry"),
                    ("UnknownPatients", "Unidentified patients"),
                    ("TheDeparted", "Departed")
                ]
            )

        elif dep.department_name == "Lab":
            links.extend([("SearchPage", "Search Patient"), ("Tests", "tests"), ("SurgeryList", "List Of Surgery")])

        elif dep.department_name == "Pharmacy":
            links.extend(
                [("SearchPage", "Search Patient"), ("MedicinesList", "Medicines")]
            )

        elif dep.department_name == "Rooms":
            links.extend(
                [
                    ("ListRoomTypes", "Room Types"),
                    ("ListRooms", "Room Management"),
                    ("PendingAdmission", "Patient Admissions"),
                ]
            )

        if dep.is_medical:
            links.extend([("DiseasesList", "List Of Diseases"), ("SurgeryList", "List Of Surgery"), ("ListOrgans", "Human organs"), ("TheDeparted", "Departed"), ("PatientsQue", "Que")])
        
        if dep.department_name == "Morgue":
            links.extend([("MorgueList", "morgue"), ('FatalityReportsList', 'fdatality reports'), ('AutopsyList', 'autopsies')])

    return links


def manage_notifications(au, flag=True):
    morelinks = {}
    morelinks["unread_messages"] = "Message"
    morelinks["announcements"] = ""
    morelinks["surgery_due"] = ""
    notis = au.get_notifications(flag)

    notis_with_links = {}
    for key in notis:
        if notis[key]:
            notis_with_links[key] = (notis[key], morelinks[key])

    if au.shift and au.shift.shift_change_due():
        next_shift = predict_shift_change().get(au.shift.shift_name)
        notis_with_links["next_shift"] = next_shift

    return notis_with_links


def department_home(request, msg = None):
    if request.user.is_superuser:
        return redirect("SelectPage4Admin")
    if request.user.is_authenticated and request.user.appuser.lock_now():
        appuser = request.user.appuser
        dep = appuser.department
        if appuser.pro_level.level_number > 3:
            appuser.lockdown = True
            appuser.save()

        data = {"dep": dep}
        if dep.is_manager(appuser):
            data["manager"] = True

        data["links"] = get_links(appuser)
        data["notifications"] = manage_notifications(appuser, True)
        data["department_home"] = True
        executives = Level.objects.filter(level_number__lt = 4)
        data["e_men"] = AppUser.objects.filter(pro_level__in = executives)

        if msg:
            data["msg"] = msg

        if request.method == "GET":
            announcement_id = request.GET.get("announcement_id")
            if announcement_id:
                data["announcement"] = Announcement.objects.get(pk=announcement_id)

        template = "Hospital/DHome.html"

        return render(request, template, data)
    else:
        return redirect("login")


def staff_home(request):
    if request.user.is_authenticated and not request.user.appuser.lockdown:
        appuser = request.user.appuser
        appuser.lockdown = False
        appuser.save()
        dep = appuser.department
        shift = appuser.shift
        data = {"links": get_links(appuser)}
        data["notifications"] = manage_notifications(appuser, False)
        if shift:
            data["current_shift"] = shift
            data["next_week_shift"] = "{0} - {1}".format(
                shift.next_turn.start_time, shift.next_turn.end_time
            )
            data["change_date"] = (shift.last_updated + timedelta(days=7)).date()
        else:
            data["current_shift"] = "no shift assigned"

        data["disc_actions"] = appuser.disciplinaryaction_set.filter(is_complete=False)

        template = "Hospital/SHome.html"
        return render(request, template, data)
    else:
        return render(
            request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
        )


def change_shift(request):
    if only_managers_of_department(request.user, Department.objects.get(department_name = 'OP')):
        shifts = Shift.objects.all()
        if shifts[0].last_updated < datetime.now(timezone.utc) - timedelta(days=7):
            sh = shifts.get(end_time = time(16))
            sh.end_time = time(5)
            sh.save()

            sh = shifts.get(end_time = time(0))
            sh.end_time = time(16)
            sh.start_time = time(8)
            sh.save()

            sh = shifts.get(end_time = time(8))
            sh.end_time = time(0)
            sh.start_time = time(16)
            sh.save()

            sh = shifts.get(end_time = time(5))
            sh.end_time = time(8)
            sh.start_time = time(0)
            sh.save()

            Shift.predict_shift_change()
            return render(request, "Hospital/shiftchange.html", {'s_msg' : 'shift changed successfully!', 'links' : get_links(request.user.appuser)})
        else:
            return render(request, "Hospital/shiftchange.html", {'r_msg' : 'you can change shift only after {0}!'.format(shifts[0].last_updated + timedelta(days=7)), 'links' : get_links(request.user.appuser)})
    else:
        return render(
            request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
        )


def new_patient(request, hr):
    if only_departments(request.user, ["OP", "Casuality"]):
        if request.method == "POST":
            form = PatientPersonalRecordForm(request.POST, request.FILES)
            sub_form_addr = AddressForm(request.POST)

            if form.is_valid():
                personal = form.save(commit=False)

                if sub_form_addr.is_valid():
                    ad = sub_form_addr.save(commit=False)
                    ad.save()
                    personal.p_address = ad
                    personal.save()

                    if hr != 0:
                        HR = PatientHealthReccord.objects.get(pk=hr)
                        if HR.patient_unknown:
                            if not personal.photo:
                                personal.photo = HR.patient_unknown.photo
                                personal.save()
                            HR.patient = personal
                            HR.save(personal)
                            if HR.patient_unknown.deceased:
                                HR.patient.deceased = True
                                HR.patient.save()
                            HR.patient_unknown.delete()
                        else:
                            pass

                return redirect("FindHealthRecords", patient=personal.pk)

            else:
                return redirect(self.request.path_info)

        else:
            form = PatientPersonalRecordForm()
            sub_form_addr = AddressForm()
            source = Test.objects.all()

        return render(
            request,
            "Hospital/signup.html",
            {
                "form": form,
                "sub_form_addr": sub_form_addr,
                "source": source,
                "base_temp": "Hospital/DBase.html",
                "head": "New Patient",
                "links" : get_links(request.user.appuser)
            },
        )
    else:
        return render(
            request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
        )


class HealthProfile(DetailView):
    model = PatientHealthReccord
    template_name = "Hospital/single_health_record.html"

    def dispatch(self, request, *args, **kwargs):
        if only_departments(request.user, ["OP", "Casuality"]):
            return super(HealthProfile, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["links"] = get_links(self.request.user.appuser)
        if data["object"].patient_unknown:
            data["unknown"] = data["object"].patient_unknown
            data["records"] = [data["object"].patient_unknown]
            data["records"].extend(list(data["object"].patientassociatedfiles_set.all()))
        else:
            data["patient"] = data["object"].patient
            data["records"] = data["object"].patientassociatedfiles_set.all()
        data["trans_docs"] = data["object"].patienttransfer_set.all()

        return data


class IdentifyUnknown(UpdateView):
    model = PatientHealthReccord
    template_name = "Hospital/UpdateWithoutDelete.html"
    fields = [
        "patient",
    ]

    def get_success_url(self):
        hr = PatientHealthReccord.objects.get(pk=self.kwargs.get("pk"))
        if hr.patient:
            return reverse("FindHealthRecords", kwargs={"patient": hr.patient.pk})
        else:
            raise HttpResponseForbidden

    def dispatch(self, request, *args, **kwargs):
        hr = PatientHealthReccord.objects.get(pk=self.kwargs.get("pk"))
        if only_departments(request.user, ["OP", "Casuality"]) and hr.patient_unknown:
            return super(IdentifyUnknown, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["base_temp"] = "Hospital/DBase.html"
        data["head"] = "Find Identity of U{0} ,aged {1}, {2}".format(data["object"].patient_unknown.id, data["object"].patient_unknown.estimated_age, data["object"].patient_unknown.patient_gentder)
        data["extra_info"] = "(hr.id : {0}) identity marks : {1}; companion name : {2}, companion phone : {3}".format(
            data["object"].id, data["object"].patient_unknown.patient_identity_marks, data["object"].companion_name, data["object"].companion_phone
        )
        data["form"].fields["patient"].queryset = PatientPersonalReccord.objects.all()
        data["links"] = get_links(self.request.user.appuser)
        return data

    def form_valid(self, form):
        hr = PatientHealthReccord.objects.get(pk=self.kwargs.get("pk"))
        pat = form.cleaned_data.get('patient')
        if not pat.patienthealthreccord_set.filter(status_code__lt = 6):
            super().form_valid(form)
            if hr.patient_unknown:
                hr.patient_unknown.delete()
        else:
            data = self.get_context_data(**self.kwargs)
            data["extra_info"] = '!!!! this patient has an active health record. if the patient is correct, please try after deleting(deactivating) old health records.  !!!!'
            return render(self.request, self.template_name, data)

        hr.refresh_from_db()

        return redirect("FindHealthRecords", patient=hr.patient.pk)


class NewUnknownPatient(CreateView):
    model = PatientUnknown
    fields = (
        "patient_identity_marks",
        "patient_gentder",
        "estimated_age",
        "other_known_informations",
        "photo",
    )
    template_name = "Hospital/signup.html"

    def dispatch(self, request, *args, **kwargs):
        if only_departments(request.user, ["OP", "Casuality"]):
            return super(NewUnknownPatient, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["sub_form"] = PatientHealthReccordForm()
        departments = Department.objects.filter(is_medical=True)
        data["sub_form"].fields["departments"].queryset = departments
        data["head"] = "New Unknown Patient"
        data["base_temp"] = "Hospital/DBase.html"
        data["links"] = get_links(self.request.user.appuser)
        return data

    def form_valid(self, form):
        PU = form.save(commit=False)

        values = self.request.POST
        hr_obj = PatientHealthReccordForm(values)
        HR = PatientHealthReccord()
        if values.get("companion_name"):
            HR.companion_name = values.get("companion_name")
        if values.get("companion_phone"):
            HR.companion_phone = values.get("companion_phone")
        if values.get("accident"):
            acc = Accident.objects.get(pk = values.get("accident"))
            HR.accident = acc

        if not hr_obj.is_valid():
            raise HttpResponseForbidden
        PU.save()
        HR.patient_unknown = PU
        HR.op_time_stamp = datetime.now()
        HR.save()
        HR.departments.set(hr_obj.cleaned_data.get("departments"))
        HR.save()

        return redirect("HealthProfile", pk=HR.id)


class UnknownPatients(TemplateView):
    template_name = "Hospital/object_list.html"

    def dispatch(self, request, *args, **kwargs):
        if only_departments(request.user, ["OP", "Casuality"]):
            return super(UnknownPatients, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )


    def get_context_data(self, **kwargs):
        data = {'object_list' : PatientHealthReccord.objects.filter(patient = None).exclude(patient_unknown = None)}
        data["special_link"] = ("NewUnknownPatient", "create new unknown patient")
        data["base_temp"] = "Hospital/DBase.html"
        data["head"] = "Unknown patients"
        data["edit_url"] = "HealthProfile"
        data["links"] = get_links(self.request.user.appuser)
        return data


class UpdateUnknownPatient(UpdateView):
    model = PatientUnknown
    fields = (
        "patient_identity_marks",
        "patient_gentder",
        "estimated_age",
        "other_known_informations",
        "photo",
    )
    
    template_name = "Hospital/UpdateWithoutDelete.html"

    def get_success_url(self):
        pu = PatientUnknown.objects.get(pk=self.kwargs.get("pk"))
        pk = pu.patienthealthreccord.pk
        return reverse("HealthProfile", kwargs={"pk": pk})

    def dispatch(self, request, *args, **kwargs):
        if only_departments(request.user, ["OP", "Casuality"]):
            return super(UpdateUnknownPatient, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["base_temp"] = "Hospital/DBase.html"
        data["links"] = get_links(self.request.user.appuser)
        return data


def patient_reception(request):
    if only_departments(request.user, ["OP", "Casuality"]):
        return render(
            request, "Hospital/OP.html", {"links": get_links(request.user.appuser)}
        )
    else:
        return render(
            request,
            "Hospital/Unauthorized.html",
            {"link": ("DHome", "Go To Home"), "er_msg": "Get Out!"},
        )


class UpdateHealthRecord(UpdateView):
    model = PatientHealthReccord
    template_name = "Hospital/Update.html"
    fields = ["departments", "companion_name", "companion_phone", "accident"]

    def get_success_url(self):
        hr = PatientHealthReccord.objects.get(pk=self.kwargs.get("pk"))
        return reverse("HealthProfile", kwargs={"pk": hr.pk})

    def dispatch(self, request, *args, **kwargs):
        if only_departments(request.user, ["OP", "Casuality"]):
            return super(UpdateHealthRecord, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["base_temp"] = "Hospital/DBase.html"
        data["links"] = get_links(self.request.user.appuser)
        data["form"].fields["departments"].queryset = Department.objects.filter(is_medical = True)
        if data["object"].patient_unknown:
            data["err_msg"] = "you cannot delete this record"
        return data
    
    def form_valid(self, form):
        hr = PatientHealthReccord.objects.get(pk = self.kwargs.get("pk"))
        if self.request.POST.get('deletable') == 'delete' and not hr.patient_unknown:
            hr.status_code = 6
            hr.save()
            hr.patient.active = False
            hr.patient.save()
            return redirect("FindHealthRecords", patient = hr.patient.id)

        else:
            super().form_valid(form)
            return redirect("HealthProfile", pk = self.kwargs.get("pk"))


class ChangePatientDetails(UpdateView):
    model = PatientPersonalReccord
    template_name = "Hospital/signup.html"
    fields = ["p_Fname", "p_Lname", "p_age", "p_gender", "phone", "photo"]

    def get_success_url(self):
        return reverse_lazy("FindHealthRecords", kwargs={"patient": self.kwargs["pk"]})

    def dispatch(self, request, *args, **kwargs):
        if only_departments(request.user, ["OP", "Casuality"]):
            return super(ChangePatientDetails, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        init_values = model_to_dict(data["object"].p_address)
        data["sub_form_addr"] = AddressForm(initial=init_values)
        data["base_temp"] = "Hospital/DBase.html"
        data["links"] = get_links(self.request.user.appuser)
        data["head"] = "change details"
        return data

    def form_valid(self, form):
        addr = AddressForm(self.request.POST)
        if addr.is_valid():
            Address.objects.filter(patientpersonalreccord=self.kwargs["pk"]).update(
                place=addr.cleaned_data.get("place"),
                zip_code=addr.cleaned_data.get("zip_code"),
                district=addr.cleaned_data.get("district"),
            )
        super().form_valid(form)
        return redirect(self.get_success_url())


class PatientSearchResultsView(ListView):
    model = PatientPersonalReccord
    template_name = "Hospital/search_results.html"

    def dispatch(self, request, *args, **kwargs):
        if only_departments(request.user, ["OP", "Casuality"]):
            return super(PatientSearchResultsView, self).dispatch(
                request, *args, **kwargs
            )
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        term = self.request.GET.get("term")

        if not term:
            return redirect("OPPage")

        if term == "all":
            queryset = PatientPersonalReccord.objects.all()

        elif is_num(term):
            term = int(term)
            queryset = PatientPersonalReccord.objects.filter(pk=term)

        else:
            queryset = PatientPersonalReccord.objects.filter(
                p_Fname__icontains=term
            ) | PatientPersonalReccord.objects.filter(p_Lname__icontains=term)

        return {"object_list": queryset, "links": get_links(self.request.user.appuser)}


def is_num(term):
    try:
        temp = int(term)
        return True
    except:
        return False


class HealthRecordSearchResultsView(CreateView):
    model = PatientHealthReccord
    template_name = "Hospital/health_records.html"
    fields = ["departments", "companion_name", "companion_phone", "accident"]

    def dispatch(self, request, *args, **kwargs):
        if only_departments(request.user, ["OP", "Casuality"]):
            return super(HealthRecordSearchResultsView, self).dispatch(
                request, *args, **kwargs
            )
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self):
        data = super().get_context_data()
        if self.kwargs.get("change_dep") == 919:
            data["dep_form"] = ChangeDepartmentForm()

        patient = self.kwargs.get("patient")
        queryset = PatientHealthReccord.objects.filter(patient_id=patient)
        data["patient"] = PatientPersonalReccord.objects.get(pk=patient)
        data["active_health_records"] = queryset.filter(status_code__lt=6)
        data["items"] = queryset.filter(status_code__gt=4)
        departments = Department.objects.filter(is_medical=True)
        data["form"].fields["departments"].queryset = departments
        data["links"] = get_links(self.request.user.appuser)
        return data

    def form_valid(self, form):
        patient = PatientPersonalReccord.objects.get(pk=self.kwargs["patient"])
        deps = form.cleaned_data.get("departments")
        if deps and not patient.deceased:
            rec = form.save(commit=False)
            rec.patient = patient
            rec.op_time_stamp = datetime.now()
            rec.save()
            rec.departments.set(deps)
            rec.save()
            patient.active = True
            patient.save()

        elif dismiss_rec_id:
            PatientHealthReccord.objects.get(pk=dismiss_rec_id).dismiss()

        return redirect(self.request.path_info)


def search_record(
    request,
):  # Strictly for doctors and nurses in charge of patient consulting and pharmacy
    if only_departments(request.user, ["Pharmacy", "Lab"]) or only_doctors(
        request.user
    ):
        au = request.user.appuser

        if request.method == "POST":
            key = int(request.POST["term"])
            try:
                patient = PatientPersonalReccord.objects.get(pk=key)
            except PatientPersonalReccord.DoesNotExist:
                return redirect("SearchPage")

            if au.check_department("Pharmacy"):
                return redirect("Pharmacy", pk=patient.id)

            elif au.check_department("Lab"):
                return redirect("TestList", pk=key)
            else:
                data = {}
                data["records"] = au.department.patienthealthreccord_set.filter(patient = patient).order_by("-op_time_stamp")
                data["link"] = "PatientReview"
                data["links"] = get_links(au)
                data['base_temp'] = "Hospital/SBase.html"
                return render(request, "Hospital/patient_review_home.html", data)

        else:
            data = {"links": get_links(au)}
            if au.lockdown:
                data['base_temp'] = "Hospital/DBase.html"
            else:
                data['base_temp'] = "Hospital/SBase.html"

            if au.check_department("Lab"):
                data["records"] = TestResults.objects.filter(time_taken=None).order_by(
                    "time_ordered"
                )

                data["link"] = "TakeTest"
            elif au.check_profession(4):
                data["records"] = au.department.patienthealthreccord_set.filter(
                    status_code=0
                ).order_by("op_time_stamp")
                data["link"] = "PatientReview"

            return render(request, "Hospital/patient_review_home.html", data)
    else:
        return render(
            request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
        )


def medicine_list(diseases):
    med_dict = {}
    for disease in diseases:
        medicines = [str(med) for med in disease.known_medicines.all()]
        med_dict[disease.pk] = simplejson.dumps(medicines)
    return med_dict


class PatientsQue(TemplateView):
    template_name = "Hospital/pat_q.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.appuser.department:
            return super(PatientsQue, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        dep = self.request.user.appuser.department
        visited_patients = dep.visited_patients.filter(status_code__lt = 6)
        waiting_patiens = dep.patienthealthreccord_set.filter(status_code__lt = 6).exclude(id__in = visited_patients).order_by("op_time_stamp")
        data = {'object_list' : waiting_patiens, "old_object_list" : visited_patients}
        if self.request.user.appuser.lockdown:
            data["base_temp"] = "Hospital/DBase.html"
        else:
            data["base_temp"] = "Hospital/SBase.html"
        data["links"] = get_links(self.request.user.appuser)
        return data


def patientreview(request, health_id):
    health_rec = PatientHealthReccord.objects.get(pk=health_id)
    if only_doctors_and_departments(
        request.user, [dep.department_name for dep in health_rec.departments.all()]
    ):

        appuser = request.user.appuser
        if request.method == "POST":
            add_disease_form = AddDiseaseForm(request.POST)
            add_test_form = AddTestsForm(request.POST)
            add_rmrk_form = AddRemarkForm(request.POST)

            if add_rmrk_form.is_valid() and add_rmrk_form.cleaned_data.get("rem_text"):
                rmrk = add_rmrk_form.save(commit=False)
                rmrk.record = health_rec
                rmrk.remark_by = appuser
                rmrk.save()

            if health_rec.status_code == 6:
                return redirect("PatientReport", pk=health_rec.pk)

            if add_disease_form.is_valid():
                health_rec.diseases.set(add_disease_form.cleaned_data.get("diseases"))
                health_rec.save()

            if add_test_form.is_valid():
                tests = add_test_form.cleaned_data.get("tests")
                for test in tests:
                    tr = TestResults.objects.get_or_create(
                        record=health_rec, test=test, time_taken=None
                    )
                    if tr[1]:
                        tr[0].issued_by = appuser
                        tr[0].save()
                        tr[0].add_to_bill()

            admit = request.POST.get("admit")
            next_visit = request.POST.get("next_visit")

            s = request.POST

            for i in range(1, 15):
                med_nam = "selected_meds" + str(i)
                med_no = "med_no" + str(i)
                med_freq = "med_freq" + str(i)

                if med_nam in s and s[med_nam]:
                    key = s[med_nam]
                    num = 0
                    freq = 0
                    med = Medicine.objects.get(pk=key)

                    if med_no in s and s[med_no]:
                        num = s[med_no]
                    if med_freq in s and s[med_freq]:
                        freq = s[med_freq]
                    pres = Prescription(
                        record=health_rec, medicine=med, med_number=num, med_freq=freq, pres_by = appuser
                    )
                    pres.save()

            if next_visit:
                health_rec.patient.next_meeting_date = next_visit
                health_rec.patient.last_visited_date = datetime.today()
                health_rec.patient.save()
            if admit == "0":
                Admission.objects.get_or_create(record=health_rec, ad_time=None)

            if admit == "3":
                a = health_rec.admission_set.filter(ad_time=None).delete()

            if health_rec.status_code == 0 or health_rec.status_code == 2:
                health_rec.status_code += 1
                health_rec.save()
            if appuser.department not in health_rec.departments_visited.all() and health_rec.status_code < 6:
                health_rec.departments_visited.add(appuser.department)
                health_rec.save()

            bill = health_rec.get_bill()
            bill.charge_for_consulting()

            return redirect("PatientReport", pk=health_rec.pk)

        else:
            data = {
                    "rec": health_rec,
                    "admitted": health_rec.admission_status(),
                    "add_rmrk_form": AddRemarkForm(),
                    "links" : get_links(appuser)
                }
            if health_rec.status_code < 6:
                add_disease_form = AddDiseaseForm(
                    initial={"diseases": health_rec.diseases.all()}
                )
                add_test_form = AddTestsForm()
                add_disease_form["diseases"].onmouseover = "f(this)"
                tests = Test.objects.all()
                tests = serialize_qs(tests, ["id", "test_name"])
                tests = simplejson.dumps(tests)

                meds = Medicine.objects.all()
                meds = serialize_qs(meds, ["id", "medicine_name", "stock_now"])
                meds = simplejson.dumps(meds)
                data["tests"] = tests
                data["meds"] = meds
                data["form"] = add_disease_form
                data["med_dict"] = medicine_list(Disease.objects.all())
                data["add_test_form"] = add_test_form

            admitted = bool(health_rec.admission_set.filter(dis_time=None))
            visit_date = (
                None
                if health_rec.patient_unknown
                else health_rec.patient.next_meeting_date
            )
            data["visit_date"] = visit_date

            return render(
                request,
                "Hospital/patient_review.html",
                data,
            )
    else:
        return render(
            request,
            "Hospital/Unauthorized.html",
            {
                "link": ("SHome", "Go Home"),
                "er_msg": "doc, this patient did not check in with OP or he is not in your department!",
            },
        )


class PatientReport(DetailView):
    model = PatientHealthReccord
    template_name = "Hospital/patient_report.html"

    def dispatch(self, request, *args, **kwargs):
        if only_medical(request.user):
            return super(PatientReport, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        appuser = self.request.user.appuser
        hr = PatientHealthReccord.objects.get(pk=self.kwargs["pk"])
        is_surgery = self.request.GET.get("surgery_required")
        if is_surgery and appuser.check_profession(4) and hr.status_code <6:
            obj = Surgery(
                record=hr, initiated_by = appuser
            )
            obj.save()

        data = super().get_context_data(**kwargs)
        record = data["object"]
        data["remarks"] = record.healthremarks_set.all()
        data["prescriptions_to_give"] = record.prescription_set.filter(is_given=False)
        data["prescriptions_given"] = record.prescription_set.filter(is_given=True)
        data["tests_not_taken"] = record.testresults_set.filter(time_taken=None)
        data["tests_taken"] = record.testresults_set.exclude(time_taken=None)
        data["surgeries"] = record.surgery_set.all()
        data["patient"] = record.patient_unknown if record.patient_unknown else record.patient
        if record.patient_unknown:
            data['unknown'] = 'unknown'
        data["doctor"] = appuser.check_profession(4) and not appuser.lockdown and appuser.department in record.departments.all()
        data["dischargable"] = (
            True if (record.admission_status() == 2 and data["doctor"]) else False
        )
        data["links"] = get_links(self.request.user.appuser)
        data['base_temp'] = 'Hospital/DBase.html' if appuser.lockdown else 'Hospital/SBase.html'
        return data


class PatientFiles(CreateView):
    model = PatientAssociatedFiles
    template_name = "Hospital/UpdateWithImages.html"
    fields = ["photo", "title"]

    def dispatch(self, request, *args, **kwargs):
        if only_departments(request.user, ["OP", "Casuality"]):
            return super(PatientFiles, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        hr = PatientHealthReccord.objects.get(
            id=self.kwargs["pk"]
        )
        files = hr.patientassociatedfiles_set.all()
        data["records"] = files
        data["head"] = "Upload Files"
        data["heading"] = "Uploaded Files Are Shown Below"
        data["base_temp"] = "Hospital/DBase.html"
        data["links"] = get_links(self.request.user.appuser)
        data['no_delete'] = True
        return data

    def form_valid(self, form):
        delete_image = self.request.POST.get("delete_image")
        hr = PatientHealthReccord.objects.get(
            id=self.kwargs["pk"]
        )
        if delete_image:
            PatientAssociatedFiles.objects.get(pk=delete_image).delete()

        else:
            title = form.cleaned_data.get("certificate_title")

            if not PatientAssociatedFiles.objects.filter(record=hr, title=title):
                obj = form.save(commit=False)
                obj.record = hr
                obj.save()

        return redirect(self.request.path_info)


class UpdateRemark(UpdateView):
    model = HealthRemarks
    fields = ["rem_text"]
    template_name = "Hospital/Update.html"

    def get_success_url(self):
        return reverse("PatientReport", kwargs={"pk": self.health_rec.pk})

    def dispatch(self, request, *args, **kwargs):
        obj = HealthRemarks.objects.get(pk=self.kwargs.get("pk"))
        if only_doctors_and_departments(request.user, [obj.remark_by.department.department_name]):
            return super(UpdateRemark, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["base_temp"] = "Hospital/SBase.html"
        data["head"] = "update health remark"
        data["links"] = get_links(self.request.user.appuser)
        return data

    def form_valid(self, form):
        pk = self.kwargs["pk"]
        self.health_rec = HealthRemarks.objects.get(pk=pk).record

        try:
            d = self.request.POST["deletable"]
            if d == "delete":
                HealthRemarks.objects.get(pk=pk).delete()

        except:
            super().form_valid(form)

        return redirect("PatientReport", pk=self.health_rec.pk)


class UpdateTest(UpdateView):
    model = TestResults
    fields = ["test"]
    template_name = "Hospital/Update.html"

    def get_success_url(self):
        return reverse("PatientReport", kwargs={"pk": self.health_rec.pk})

    def dispatch(self, request, *args, **kwargs):
        obj = TestResults.objects.get(pk=self.kwargs.get("pk"))
        if (not obj.time_taken) and only_doctors_and_departments(request.user, [obj.issued_by.department.department_name]):
            return super(UpdateTest, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["base_temp"] = "Hospital/SBase.html"
        data["links"] = get_links(self.request.user.appuser)
        return data

    def form_valid(self, form):
        pk = self.kwargs["pk"]
        tr = TestResults.objects.get(pk=pk)
        self.health_rec = tr.record

        d = self.request.POST.get("deletable")
        if d == "delete" and not tr.time_taken:
            tr.deduct_from_bill()
            tr.delete()
        else:
            old_amnt = tr.test.test_amnt
            super().form_valid(form)
            tr.refresh_from_db()
            new_amnt = tr.test.test_amnt
            tr.alter_amnt(old_amnt, new_amnt)

        return redirect("PatientReport", pk=self.health_rec.pk)


class UpdatePrescription(UpdateView):
    model = Prescription
    fields = ["medicine", "med_number", "med_freq"]
    template_name = "Hospital/Update.html"

    def get_success_url(self):
        return reverse("PatientReport", kwargs={"pk": self.health_rec.pk})

    def dispatch(self, request, *args, **kwargs):
        obj = Prescription.objects.get(pk=self.kwargs.get("pk"))
        if (not obj.is_given) and only_doctors_and_departments(request.user, [obj.pres_by.department.department_name]):
            return super(UpdatePrescription, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["base_temp"] = "Hospital/SBase.html"
        data["links"] = get_links(self.request.user.appuser)
        return data

    def form_valid(self, form):
        pk = self.kwargs["pk"]
        self.health_rec = Prescription.objects.get(pk=pk).record
        pres = Prescription.objects.get(pk=pk)

        try:
            d = self.request.POST["deletable"]
            if d == "delete" and not pres.is_given:
                pres.delete()

        except:
            super().form_valid(form)
            pres.refresh_from_db()
        return redirect("PatientReport", pk=self.health_rec.pk)


class ListUnknowns(TemplateView):
    model = PatientHealthReccord
    template_name = "Hospital/object_list.html"

    def dispatch(self, request, *args, **kwargs):
        if only_departments(
            request.user, ["Casuality", "OP", "Pharmacy", "Lab"]
        ) or only_doctors(request.user):
            return super(ListUnknowns, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        au = self.request.user.appuser
        data = {}
        data["object_list"] = PatientHealthReccord.objects.filter(
            patient = None)
        if au.lockdown:
            data["base_temp"] = "Hospital/DBase.html"
        else:
            data["base_temp"] = "Hospital/SBase.html"
        data["head"] = "Unknown patients"
        data["links"] = get_links(au)

        if au.check_profession(4):
            data["edit_url"] = "PatientReview"
        elif au.check_department("Casuality") or au.check_department("OP"):
            data["edit_url"] = "HealthProfile"
        elif au.check_department("Pharmacy"):
            data["edit_url"] = "Pharmacy"
        elif au.check_department("Lab"):
            data["edit_url"] = "TestList"

        return data


def pharmacy(request, pk):
    if only_department(request.user, "Pharmacy"):
        er = ""
        template_name = "Hospital/patient_medicines.html"
        patient = PatientPersonalReccord.objects.filter(pk=pk)
        if patient:
            patient = patient[0]
            rec = patient.patienthealthreccord_set.filter(status_code__lt=6).order_by("op_time_stamp").reverse()
            if rec:
                rec = rec[0]
            else:
                raise Http404
        else:
            rec = PatientHealthReccord.objects.filter(pk=pk)
            if rec and rec[0].patient_unknown:
                rec = rec[0]
            else:
                raise Http404

        bill = rec.get_bill()

        prescriptions = rec.prescription_set.filter(is_given=False, canceled=False)
        bill_items = rec.prescription_set.all()

        if request.method == "POST":
            i = 1
            post_data = request.POST

            counter = len(prescriptions) + 1
            for i in range(0, counter):
                if str(i) in post_data:
                    key = int(post_data[str(i)])
                    pres = prescriptions.get(pk=key)
                    medicine = pres.medicine
                    if medicine.reduce_stock(pres.med_number * pres.med_freq):
                        pres.add_to_bill()
                    else:
                        er = "Not enough number of {0}".format(medicine.medicine_name)

                    prescriptions = rec.prescription_set.filter(
                        is_given=False, canceled=False
                    )
            bill.refresh_from_db()

        return render(
            request,
            template_name,
            {
                "prescriptions": prescriptions,
                "bill_items": bill_items,
                "bill": bill,
                "er": er,
                "links" : get_links(request.user.appuser),
            },
        )

    else:
        return render(
            request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
        )


def discharge(request, p_id):
    patient = PatientHealthReccord.objects.get(id=p_id)
    room = patient.admission_set.exclude(ad_time = None).filter(dis_time = None)
    if room:
        room = room[0]
    if only_doctors_and_departments(request.user, [dep.department_name for dep in patient.departments.all()]):
        if request.method == "POST":
            adm = request.POST.get("admission")
            if adm == "Discharge":
                obj = patient.admission_set.exclude(ad_time=None).get(dis_time=None)
                patient.discharge(obj)

        return render(
            request,
            "Hospital/discharge.html",
            {
                "links": get_links(request.user.appuser),
                "patient": patient,
                "dis": patient.admission_status() == (0 or 3),
                "room" : room,
                "tests_due" : patient.testresults_set.filter(time_taken = None),
                "surgeries_due" : patient.surgery_set.filter(end_date = None, end_time = None)
            },
        )

    else:
        return render(
            request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
        )


class Tests(TemplateView):
    template_name = "Hospital/object_list.html"

    def dispatch(self, request, *args, **kwargs):
        if only_department(request.user, "Lab"):
            return super(Tests, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = {'object_list' : Test.objects.all()}
        data["base_temp"] = "Hospital/DBase.html"
        data["edit_url"] = "EditTest"
        data["head"] = "Tests"
        data["special_link"] = ("NewTest", "add new test")
        data["links"] = get_links(self.request.user.appuser)
        return data


class NewTest(CreateView):
    model = Test
    template_name = "Hospital/Create.html"
    fields = ["test_name", "test_abbr", "test_description", "test_amnt"]
    success_url = reverse_lazy("Tests")

    def dispatch(self, request, *args, **kwargs):
        if only_department(request.user, "Lab"):
            return super(NewTest, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["base_temp"] = "Hospital/DBase.html"
        data["head"] = "add new test"
        data["links"] = get_links(self.request.user.appuser)
        return data


class EditTest(UpdateView):
    model = Test
    template_name = "Hospital/Update.html"
    fields = ["test_name", "test_abbr", "test_description", "test_amnt"]
    success_url = reverse_lazy("Tests")

    def dispatch(self, request, *args, **kwargs):
        if only_department(request.user, "Lab"):
            return super(EditTest, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["base_temp"] = "Hospital/DBase.html"
        data["head"] = "edit test"
        data["links"] = get_links(self.request.user.appuser)
        return data
    
    def form_valid(self, form):
        test = Test.objects.get(pk = self.kwargs.get("pk"))
        dele = self.request.POST.get('deletable')
        if dele:
            if test.testresults_set.count() < 1:
                test.delete()
            else:
                data = self.get_context_data(**self.kwargs)
                data['err_msg'] = "{0} patients have taken this test. you cannot delete a test that is taken by at least one person".format(test.testresults_set.count())
                return render(self.request, self.template_name, data)
        else:
            super().form_valid(form)
        return redirect("Tests")


class TestList(ListView):
    model = TestResults
    template_name = "Hospital/object_list.html"

    def dispatch(self, request, *args, **kwargs):
        if only_department(request.user, "Lab"):
            return super(TestList, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        patient = PatientPersonalReccord.objects.filter(pk=self.kwargs["pk"])
        if patient:
            patient = patient[0]
            hr = patient.get_active_health_reccord_or_last()
        else:
            hr = PatientHealthReccord.objects.get(pk=self.kwargs["pk"])

        object_list = []
        if hr:
            object_list = hr.testresults_set.filter(time_taken=None)
            if hr.patient:
                all_hrs = patient.patienthealthreccord_set.all()

                old_object_list = TestResults.objects.filter(
                    record__id__in=all_hrs
                ).exclude(time_taken=None)
            else:
                old_object_list = hr.testresults_set.filter(record=hr).exclude(
                    time_taken=None
                )

            data = {
                "object_list": object_list,
                "old_object_list": old_object_list,
                "base_temp": "Hospital/DBase.html",
                "head": "{0} Tests to Take".format(
                    hr.patient
                    if hr.patient
                    else ("U{0}".format(hr.patient_unknown.id) if hr.patient_unknown else "No")
                ),
                "head2": "Completed Tests",
                "edit_url": "TakeTest",
                "edit_url2": "TakeTest",
                "links": get_links(self.request.user.appuser),
                "special_link2": (
                    reverse("TestHistory", kwargs={"pk": patient.pk}),
                    "test history",
                )
                if patient
                else "",
            }
        else:
            data = {
                "base_temp": "Hospital/DBase.html",
                "head": "no tests to take",
                "head2": "Completed Tests",
                "links": get_links(self.request.user.appuser),
            }

        return data


class TakeTest(CreateView):
    template_name = "Hospital/test_report_writing.html"
    model = TRDocuments
    fields = ["title", "photo"]

    def dispatch(self, request, *args, **kwargs):
        if only_department(request.user, "Lab"):
            return super(TakeTest, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        tr = TestResults.objects.get(pk=self.kwargs["pk"])
        trds = tr.trdocuments_set.all()
        data["tr"] = tr
        data["records"] = trds
        data["heading"] = "Uploaded Documents Are Shown Below"
        data["remark"] = tr.remarks
        data["links"] = get_links(self.request.user.appuser)
        return data

    def form_valid(self, form):
        delete_image = self.request.POST.get("delete_image")
        if delete_image:
            TRDocuments.objects.get(pk=delete_image).delete()
        else:
            tr = TestResults.objects.get(pk=self.kwargs["pk"])
            rmrk = self.request.POST.get("rmrk")
            if rmrk:
                tr.remarks = rmrk
                tr.save()
            if form.cleaned_data.get("photo"):
                trd = form.save(commit=False)
                trd.tr = tr
                trd.save()

            if self.request.POST.get("timestamp"):
                tr.stamp_time()

        return redirect(self.request.path_info)


class TestReport(DetailView):
    model = TestResults
    template_name = "Hospital/test_report.html"

    def dispatch(self, request, *args, **kwargs):
        if only_department(request.user, "Lab") or only_medical(request.user):
            return super(TestReport, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        au = self.request.user.appuser
        data = super().get_context_data(**kwargs)
        trds = data["object"].trdocuments_set.all()
        if au.check_department("Lab"):
            data["islab"] = True
        data["records"] = trds
        data["patient"] = data["object"].record.patient
        if au.lockdown:
            data['base_temp'] = 'Hospital/DBase.html'
        else:
            data['base_temp'] = 'Hospital/SBase.html'
        data["links"] = get_links(au)
        return data


class TestHistory(TemplateView):
    template_name = "Hospital/object_list.html"

    def dispatch(self, request, *args, **kwargs):
        if only_department(self.request.user, "Lab"):
            return super(TestHistory, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        patient = PatientPersonalReccord.objects.get(pk=self.kwargs.get("pk"))
        data = {}
        data["base_temp"] = "Hospital/DBase.html"
        data["object_list"] = (
            TestResults.objects.select_related("record__patient")
            .filter(record__patient=patient)
            .exclude(time_taken=None)
        )
        data["edit_url"] = "TestReport"
        data["links"] = get_links(self.request.user.appuser)
        data["head"] = "testing history"
        return data


class InitiateSurgery(UpdateView):
    template_name = "Hospital/surgery_form.html"
    model = Surgery
    fields = [
        "surgery_name",
        "team_leader",
        "team",
        "theatre",
        "total_amnt",
        "prepay_amnt",
        "start_time",
        "date_of_surgery",
        "patient_report_time",
        "team_report_time",
        "organ_under_surgery",
    ]

    def get_success_url(self):
        return self.request.path_info

    def dispatch(self, request, *args, **kwargs):
        sur = Surgery.objects.get(pk = self.kwargs.get('pk'))
        if surgery_key_control(self.request.user, sur):
            return super(InitiateSurgery, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        staffs = AppUser.objects.filter(occupabili = True).exclude(department = None)
        data['form'].fields["team_leader"].queryset = staffs
        data['form'].fields["team"].queryset = staffs
        data["docs_form"] = SurgeryDocsForm()
        data["links"] = get_links(self.request.user.appuser)
        if data['object'].is_autopsy:
            data['fatality'] = data['object'].fatality_set.all()[0] if data['object'].fatality_set.all() else False
        return data

    def form_valid(self, form):
        deleterecord = self.request.POST.get("deleterecord")
        sur = Surgery.objects.get(pk=self.kwargs["pk"])
        if deleterecord == "99":
            if not sur.end_time:
                rec = sur.record
                sur.deduct_from_bill()
                sur.delete()
                if sur.is_autopsy:
                    fates = rec.fatality_set.all()
                    return redirect("FatalityReport", pk=fates[0].pk)                    
                return redirect("PatientReport", pk=rec.pk)
            else:
                return HttpResponseForbidden()

        doc_form = SurgeryDocsForm(self.request.POST, self.request.FILES)
        if doc_form.is_valid():
            surgery = Surgery.objects.get(pk=self.kwargs["pk"])
            doc = SurgeryDocuments(
                surgery=surgery, title=doc_form.cleaned_data.get("title")
            )
            doc.photo = doc_form.cleaned_data.get("photo")
            doc.save()

        del_img = self.request.POST.get("delete_image")
        if del_img:
            SurgeryDocuments.objects.get(pk=del_img).delete()

        old_bill_amnt = sur.total_amnt

        team = form.cleaned_data.get("team")

        super().form_valid(form)
        sur.refresh_from_db()
        if sur.team_leader not in sur.team.all():
            sur.team.add(sur.team_leader)
            sur.save()
            sur.refresh_from_db()
        new_bill_amnt = sur.total_amnt
        sur.alter_amnt(old_bill_amnt, new_bill_amnt)

        data = self.get_context_data(**self.kwargs)
        data['su_msg'] = 'data updated successfully'
        return render(self.request, self.template_name, data)


class UploadSurgeryDocs(CreateView):
    model = SurgeryDocuments
    fields = ['title', 'photo']
    template_name = 'Hospital/SurgeryDocsUpload.html'

    def dispatch(self, request, *args, **kwargs):
        sur = Surgery.objects.get(pk = self.kwargs.get('pk'))
        if surgery_info_control(request.user, sur) or surgery_key_control(request.user, sur):
            return super(UploadSurgeryDocs, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['sur'] = Surgery.objects.get(pk = self.kwargs.get('pk'))
        data['links'] = get_links(self.request.user.appuser)
        data['records'] = data['sur'].surgerydocuments_set.all()
        if self.request.user.appuser.lockdown:
            data['base_temp'] = 'Hospital/DBase.html'
        else:
            data['base_temp'] = 'Hospital/SBase.html'

        if data['sur'].is_autopsy:
            data['fatality'] = data['sur'].fatality_set.all()[0] if data['sur'].fatality_set.all() else False
        return data
    
    def form_valid(self, form):
        sur = Surgery.objects.get(pk = self.kwargs.get('pk'))
        sur_doc = form.save(commit = False)
        sur_doc.surgery = sur
        sur_doc.save()

        delete_image = self.request.POST.get("delete_image")
        if delete_image:
            SurgeryDocuments.objects.get(pk=delete_image).delete()

        return redirect(self.request.path_info)


def bundle_message(appuser, recievers, object):
    text = "You are part of the team for '{0}' surgery for '{1}' at {2}. You will find further details in your department.".format(
        object.surgery_name,
        object.record,
        object.start_time if object.start_time else "undecided",
    )
    for reciever in recievers:
        msg = EMessage(sender=appuser, reciever=reciever, text=text)
        msg.save()


class SurgeryList(TemplateView):
    template_name = "Hospital/surgeries_list.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return super(SurgeryList, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = {}
        au = self.request.user.appuser
        if self.request.user.appuser.lockdown:
            data["base_temp"] = "Hospital/DBase.html"
        else:
            data["base_temp"] = "Hospital/SBase.html"

        if only_doctors(self.request.user):
            data["special_link"] = ("SearchPage", "Find Patients")
            data['edit_url'] = 'SurgeryReport'
        elif only_medical(au.app_user):
            data['edit_url'] = 'SurgeryReport'

        data["object_list"] = Surgery.objects.exclude(is_autopsy = True).order_by("date_of_surgery").reverse()
        data["head"] = "Surgeries"
        data["links"] = get_links(au)
        return data


class SurgeryReport(DetailView):
    model = Surgery
    template_name = "Hospital/surgery_report.html"

    def dispatch(self, request, *args, **kwargs):
        if only_medical(request.user):
            return super(SurgeryReport, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["patient"] = data["object"].record.patient
        if not data["patient"]:
            data["patient_unknown"] = data["object"].record.patient_unknown
        data["uploaded_files"] = data["object"].surgerydocuments_set.all()
        data["links"] = get_links(self.request.user.appuser)
        if self.request.user.appuser.lockdown:
            data["base_temp"] = "Hospital/DBase.html"
        else:
            data["base_temp"] = "Hospital/SBase.html"
        data["control"] = 1 if surgery_key_control(self.request.user, data['object']) else (2 if surgery_info_control(self.request.user, data['object']) else 3)

        return data


class WriteSurgeryReport(UpdateView):
    model = Surgery
    template_name = "Hospital/write_sur_report.html"
    fields = ("end_date", "end_time", "surgery_report")

    def get_success_url(self):
        return reverse_lazy("SurgeryReport", kwargs={"pk": self.kwargs.get("pk")})

    def dispatch(self, request, *args, **kwargs):
        sur = Surgery.objects.get(pk = self.kwargs.get('pk'))
        if surgery_key_control(request.user, sur):
            return super(WriteSurgeryReport, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["head"] = "Write Surgery Report : Surgery[ {0} ]".format(data["object"])
        data["base_temp"] = "Hospital/SBase.html"
        data["links"] = get_links(self.request.user.appuser)
        return data


class SurgeryPrepayment(UpdateView):
    model = Surgery
    fields = ["is_prepaid"]
    template_name = "Hospital/surgery_prepay.html"

    def dispatch(self, request, *args, **kwargs):
        if only_department(request.user, "Pharmacy"):
            return super(SurgeryPrepayment, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )
    
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["links"] = get_links(self.request.user.appuser)
        return data

    def form_valid(self, form):
        sur = Surgery.objects.get(pk=self.kwargs["pk"])
        req = self.request
        amnt = req.POST.get("prepay_amount")
        if amnt and (sur.prepay_amnt == Decimal(amnt)):
            sur.prepay()

        return redirect("SurgeryPrepayment", pk = sur.id)


class NewRoomType(CreateView):
    model = RoomType
    fields = ['type_name', 'daily_charge', 'max_beds']
    template_name = "Hospital/Create.html"
    success_url = reverse_lazy('ListRoomTypes')

    def dispatch(self, request, *args, **kwargs):
        if only_department(request.user, "Rooms"):
            return super(NewRoomType, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['head'] = "new room type"
        data['base_temp'] = "Hospital/DBase.html"
        data['links'] = get_links(self.request.user.appuser)
        return data


class ListRoomTypes(TemplateView):
    template_name = "Hospital/object_list.html"

    def dispatch(self, request, *args, **kwargs):
        if only_department(request.user, "Rooms"):
            return super(ListRoomTypes, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = {'object_list' : RoomType.objects.all(), 'edit_url' : 'EditRoomType'}
        data['head'] = "types of rooms"
        data['base_temp'] = "Hospital/DBase.html"
        data['links'] = get_links(self.request.user.appuser)
        data['special_link'] = ('NewRoomType', 'new room types')
        return data


class EditRoomType(UpdateView):
    model = RoomType
    fields = ['type_name', 'daily_charge', 'max_beds']
    template_name = "Hospital/Update.html"
    success_url = 'ListRoomTypes'

    def dispatch(self, request, *args, **kwargs):
        if only_department(request.user, "Rooms"):
            return super(EditRoomType, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        rt = RoomType.objects.get(pk = self.kwargs.get('pk'))
        data['head'] = "room type : {0} [total rooms - {1}]".format(rt.type_name, rt.room_set.count())
        data['base_temp'] = "Hospital/DBase.html"
        data['links'] = get_links(self.request.user.appuser)
        return data
    
    def form_valid(self, form):
        dele = self.request.POST.get('deletable')
        rt = RoomType.objects.get(pk = self.kwargs.get('pk'))
        if dele:
            if rt.room_set.count()<1:
                rt.delete()
            else:
                data = self.get_context_data(**self.kwargs)
                data["err_msg"] = "cannot delete while there are rooms of this type."
                return render(self.request, self.template_name, data)
        else:
            super().form_valid(form)
        return redirect('ListRoomTypes')
    

class NewRoom(CreateView):
    template_name = "Hospital/Create.html"
    model = Room
    fields = ["room_no", "roomtype", "vacant_beds"]

    def get_success_url(self):
        return reverse_lazy("ListRooms")

    def dispatch(self, request, *args, **kwargs):
        if only_department(request.user, "Rooms"):
            return super(NewRoom, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["base_temp"] = "Hospital/DBase.html"
        data["head"] = "Add New Room"
        data["links"] = get_links(self.request.user.appuser)
        return data

    def form_valid(self, form):
        vacant_beds = form.cleaned_data.get("vacant_beds")
        if vacant_beds <= form.cleaned_data.get("roomtype").max_beds:
            super().form_valid(form)
        return redirect(self.get_success_url())


class ListRooms(ListView):
    model = Room
    template_name = "Hospital/object_list.html"

    def dispatch(self, request, *args, **kwargs):
        if only_department(request.user, "Rooms"):
            return super(ListRooms, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        object_list = Room.objects.all()
        return {
            "head": "Rooms",
            "object_list": object_list,
            "special_link": ("NewRoom", "New Room"),
            "edit_url": "EditRoom",
            "base_temp": "Hospital/DBase.html",
            "links": get_links(self.request.user.appuser),
        }


class RoomUpdate(UpdateView):
    model = Room
    fields = ["room_no", "vacant_beds"]
    template_name = "Hospital/Update.html"

    def get_success_url(self):
        return reverse_lazy("ListRooms")

    def dispatch(self, request, *args, **kwargs):
        if only_department(request.user, "Rooms"):
            return super(RoomUpdate, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["base_temp"] = "Hospital/DBase.html"
        data["links"] = get_links(self.request.user.appuser)
        return data

    def form_valid(self, form):
        room = Room.objects.get(pk=self.kwargs["pk"])
        d = self.request.POST.get("deletable")

        if d == "delete" and room.vacant_beds == room.roomtype.max_beds:
            room.delete()
            return redirect("NewRoom")

        vacant_beds = form.cleaned_data.get("vacant_beds")
        if (
            room.roomtype.max_beds - room.vacant_beds
        ) <= vacant_beds and vacant_beds <= room.roomtype.max_beds:
            super().form_valid(form)

        return redirect(self.request.path_info)


class PatientAdmission(UpdateView):
    model = Admission
    template_name = "Hospital/patient_admission.html"
    fields = ["room"]

    def dispatch(self, request, *args, **kwargs):
        if only_department(request.user, "Rooms"):
            return super(PatientAdmission, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["links"] = get_links(self.request.user.appuser)
        return data

    def form_valid(self, form):
        obj = form.save(commit=False)
        if obj.dis_time:
            return redirect(self.request.path_info)

        adm = self.request.POST.get("Admission")
        if adm == "Admit":
            if not obj.record.admit(obj):
                return HttpResponse("Room no.{0} is full".format(obj.room.room_no))

        return redirect("AdmissionDetails", pk = obj.id)


class ListAdmissions(ListView):
    model = Admission
    template_name = "Hospital/all_admissions.html"

    def dispatch(self, request, *args, **kwargs):
        if only_department(request.user, "Rooms"):
            return super(ListAdmissions, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        term = self.request.GET.get("term")
        opt = self.kwargs.get("opt")

        if opt == 0:  # Active Room Admissions
            queryset = Admission.objects.filter(dis_time=None).exclude(ad_time=None)
        elif opt == 1:  # Checked out Rooms
            queryset = Admission.objects.exclude(dis_time=None)
        else:  # Patients waiting for admission
            queryset = Admission.objects.filter(dis_time=None, ad_time=None, )

        if term:
            queryset = queryset.select_related("record__patient").filter(
                record__patient=int(term)
            )

        return {"object_list": queryset, "links": get_links(self.request.user.appuser)}


class AdmissionDetails(TemplateView):
    template_name = "Hospital/admission_single.html"
    def dispatch(self, request, *args, **kwargs):
        if only_department(request.user, "Rooms"):
            return super(AdmissionDetails, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        return {'object' : Admission.objects.get(pk = self.kwargs.get("pk")), 'links' : get_links(self.request.user.appuser)}


class ChangeRoom(UpdateView):
    model = Admission
    template_name = "Hospital/room2room.html"
    fields = ("room",)

    def dispatch(self, request, *args, **kwargs):
        if only_department(request.user, "Rooms"):
            obj = Admission.objects.get(pk=self.kwargs["pk"])
            if obj.dis_time:
                return redirect("PendingAdmission")
            return super(ChangeRoom, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["links"] = get_links(self.request.user.appuser)
        return data

    def form_valid(self, form):
        old_adm = Admission.objects.get(pk=self.kwargs.get("pk"))
        hr = old_adm.record

        adm = Admission(record=hr, room=form.cleaned_data["room"],)
        if adm.room == old_adm.room:
            return redirect(self.request.path_info)

        hr.check_out(old_adm)
        if hr.admit(adm):
            return redirect("AdmissionDetails", pk=adm.id)
        else:
            return HttpResponse("Room no.{0} is full".format(adm.room.room_no))


class BillPayment(UpdateView):
    model = Bill
    fields = ["deductions"]
    template_name = "Hospital/bill_payment.html"

    def dispatch(self, request, *args, **kwargs):
        if only_department(request.user, "Pharmacy"):
            return super(BillPayment, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["object"].refresh_bill()
        bill = data["object"]
        data["object"].refresh_bill()
        data["patient"] = bill.record
        data["due"] = bill.total_amt_so_far - bill.total_payed - bill.deductions
        if data["due"] > 0:
            data["surs"] = bill.record.surgery_set.filter(is_prepaid=False, prepay_amnt__gt = 0)
        data["links"] = get_links(self.request.user.appuser)
        if data["patient"].patient_unknown:
            data['er_msg'] = "this person is unidentified. He/She cannot be allowed to leave hospital without resolving identity!"
        
        pat = data['patient'].patient

        data['unpaid_bills'] = []
        if pat:
            for hr in pat.patienthealthreccord_set.exclude(id = data['object'].record.id):
                bill = hr.get_bill()
                if not bill.payment_complete():
                    data['unpaid_bills'].append(bill)

        return data

    def form_valid(self, form):
        deductions = form.cleaned_data.get("deductions")
        bill = Bill.objects.get(pk=self.kwargs["pk"])
        bill.deductions = deductions
        bill.save()

        amount = int(self.request.POST.get("amount"))
        bill.pay(amount)
        rec = bill.record
        if rec.admission_status() == 3 or rec.admission_status() == 0 and rec.patient:
            rec.leave()
        
        data = {'payed_amnt' : amount, 'patient' : rec, "links" : get_links(self.request.user.appuser)}
        if amount < 0:
            data['payed_amnt'] *= -1
            data['neg'] = True
        return render(self.request, "Hospital/recipt.html", data)


class TransferPatient(CreateView):
    model = PatientTransfer
    template_name = "Hospital/create.html"
    fields = ["outwrad", "remarks", "transfer_time"]

    def dispatch(self, request, *args, **kwargs):
        if only_departments(request.user, ["OP", "Casuality"]):
            return super(TransferPatient, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        hr = PatientHealthReccord.objects.get(id=self.kwargs["p_id"])
        data["head"] = "Transfer Record For {0}".format(
            hr.patient if hr.patient else hr.patient_unknown
        )
        data["base_temp"] = "Hospital/DBase.html"
        data["links"] = get_links(self.request.user.appuser)
        return data

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.record = PatientHealthReccord.objects.get(id=self.kwargs["p_id"])
        obj.save()
        return redirect("HealthProfile", pk = self.kwargs.get("p_id"))


class EditTransferPatient(UpdateView):
    model = PatientTransfer
    template_name = "Hospital/Update.html"
    fields = ["outwrad", "remarks", "transfer_time"]

    def get_success_url(self):
        obj = PatientTransfer.objects.get(id=self.kwargs["pk"])
        return reverse_lazy("HealthProfile", kwargs = {'pk' : obj.record.id})

    def dispatch(self, request, *args, **kwargs):
        if only_departments(request.user, ["OP", "Casuality"]):
            return super(EditTransferPatient, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["base_temp"] = "Hospital/DBase.html"
        data["links"] = get_links(self.request.user.appuser)
        return data

    def form_valid(self, form):
        obj = PatientTransfer.objects.get(id=self.kwargs["pk"])
        pk = obj.record.id
        if self.request.POST.get("deletable"):
            obj.delete()
        else:
            super().form_valid(form)
        return redirect("HealthProfile", pk = pk)


class DocumentDisease(CreateView):
    model = Disease
    template_name = "Hospital/documentdisease.html"
    fields = ["disease_name", "remarks", "affected_organs", "fatality_rate", "known_medicines", "causes"]
    success_url = reverse_lazy("DiseasesList")

    def dispatch(self, request, *args, **kwargs):
        if only_medical_departments(request.user):
            return super(DocumentDisease, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["links"] = get_links(self.request.user.appuser)
        return data


class DiseasesList(ListView):
    model = Disease
    template_name = "Hospital/object_list.html"

    def dispatch(self, request, *args, **kwargs):
        if only_medical_departments(request.user):
            return super(DiseasesList, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        return {
            "edit_url": "UpdateDocumentDisease",
            "object_list": Disease.objects.all(),
            "head": "List Of Diseases",
            "base_temp": "Hospital/DBase.html",
            "special_link": ("DocumentDisease", "Document New Disease"),
            "special_link2" : (reverse("ListDiseaseCauses"), 'Causes of various diseases'),
            "links": get_links(self.request.user.appuser),
        }


class UpdateDocumentDisease(UpdateView):
    model = Disease
    template_name = "Hospital/documentdisease.html"
    fields = ["disease_name", "remarks", "affected_organs", "fatality_rate", "known_medicines", "causes"]
    success_url = reverse_lazy("DiseasesList")

    def dispatch(self, request, *args, **kwargs):
        if only_medical_departments(request.user):
            return super(UpdateDocumentDisease, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["base_temp"] = "Hospital/DBase.html"
        data["links"] = get_links(self.request.user.appuser)
        if data['object'].patienthealthreccord_set.count() > 0:
            data['err_msg'] = "you cannot delete this disease because there is {0} health reccords affiliated to this.".format(data['object'].patienthealthreccord_set.count())
        return data

    def form_valid(self, form):
        d = self.request.POST.get("deletable")
        dis = Disease.objects.get(pk=self.kwargs["pk"])
        if d == "delete" and dis.patienthealthreccord_set.count() < 1:
            dis.delete()
            return redirect("DiseasesList")

        else:
            super().form_valid(form)

        return redirect("DiseasesList")


class CreateCause(CreateView):
    model = CauseOfDisease
    fields = ['cause_name', 'cause_description']
    template_name = 'Hospital/create.html'

    def dispatch(self, request, *args, **kwargs):
        if only_medical_departments(request.user):
            return super(CreateCause, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['base_temp'] = 'Hospital/DBase.html'
        data['head'] = 'causes of diseases'
        data['links'] = get_links(self.request.user.appuser)
        return data
    
    def form_valid(self, form):
        form.save()
        if self.kwargs.get('redir') <= 0:
            return redirect("DocumentDisease")
        elif self.kwargs.get('redir'):
            return redirect('UpdateDocumentDisease', pk = self.kwargs.get('redir'))
        else:
            return redirect("ListDiseaseCauses")


class UpdateCause(UpdateView):
    model = CauseOfDisease
    fields = ['cause_name', 'cause_description']
    template_name = 'Hospital/Update.html'
    success_url = reverse_lazy("ListDiseaseCauses")

    def dispatch(self, request, *args, **kwargs):
        if only_medical_departments(request.user):
            return super(UpdateCause, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['base_temp'] = 'Hospital/DBase.html'
        data['head'] = 'cause for diseases'
        data['links'] = get_links(self.request.user.appuser)
        if data['object'].disease_set.count() > 0:
            data['err_msg'] = "you cannot delete this cause because there is {0} diseases affiliated to this.".format(data['object'].disease_set.count())
        return data

    def form_valid(self, form):
        d = self.request.POST.get("deletable")
        cau = CauseOfDisease.objects.get(pk=self.kwargs["pk"])
        if d == "delete" and cau.disease_set.count() < 1:
            cau.delete()
            return redirect("ListDiseaseCauses")

        else:
            super().form_valid(form)

        return redirect("ListDiseaseCauses")


class ListDiseaseCauses(TemplateView):
    template_name = 'Hospital/object_list.html'
    
    def dispatch(self, request, *args, **kwargs):
        if only_medical_departments(request.user):
            return super(ListDiseaseCauses, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = {}
        term = self.request.GET.get('term')
        if term:
            terms_list = term.split(' ')

        data['base_temp'] = 'Hospital/DBase.html'
        data['head'] = 'causes of diseases'
        data['object_list'] = CauseOfDisease.objects.all()
        data['edit_url'] = 'UpdateCause'
        data['special_link'] = ('CreateCause', 'document new causes')
        data['links'] = get_links(self.request.user.appuser)
        return data


class DocumentMedicine(CreateView):
    model = Medicine
    template_name = "Hospital/create.html"
    fields = ["medicine_name", "amnt_for_one", "stock_now", "last_refill_date"]
    success_url = reverse_lazy("MedicinesList")

    def dispatch(self, request, *args, **kwargs):
        if only_department(request.user, "Pharmacy"):
            return super(DocumentMedicine, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["head"] = "Documenting Medicines"
        data["base_temp"] = "Hospital/DBase.html"
        data["links"] = get_links(self.request.user.appuser)
        return data


class MedicinesList(ListView):
    model = Disease
    template_name = "Hospital/object_list.html"

    def dispatch(self, request, *args, **kwargs):
        if only_department(request.user, "Pharmacy"):
            return super(MedicinesList, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        return {
            "edit_url": "UpdateDocumentMedicine",
            "object_list": Medicine.objects.all(),
            "head": "List Of Medicines",
            "base_temp": "Hospital/DBase.html",
            "special_link": ("DocumentMedicine", "Document New Medicine"),
            "links": get_links(self.request.user.appuser),
        }


class UpdateDocumentMedicine(UpdateView):
    model = Medicine
    template_name = "Hospital/Update.html"
    fields = ["medicine_name", "amnt_for_one", "stock_now", "last_refill_date"]

    success_url = reverse_lazy("MedicinesList")

    def dispatch(self, request, *args, **kwargs):
        if only_department(request.user, "Pharmacy"):
            return super(UpdateDocumentMedicine, self).dispatch(
                request, *args, **kwargs
            )
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["base_temp"] = "Hospital/DBase.html"
        data["links"] = get_links(self.request.user.appuser)
        if data["object"].prescription_set.count() > 0:
            data["err_msg"] = "you cannot delete this medicine since there are {0} prescriptions for this".format(data["object"].prescription_set.count())
        return data

    def form_valid(self, form):
        d = self.request.POST.get("deletable")
        m = Medicine.objects.get(pk=self.kwargs["pk"])
        if d == "delete" and m.prescription_set.count() < 1:
            m.delete()
            return redirect("MedicinesList")

        else:
            super().form_valid(form)

        return redirect("MedicinesList")


class Inbox(ListView):
    model = EMessage
    template_name = "Hospital/message_list.html"

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return super(Inbox, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        appuser = self.request.user.appuser
        department = appuser.department
        if appuser.lockdown:
            queryset = {
                "unread":department.emessage_set.filter(
                    personal=False,
                    read_time=None,
                ),
                "base_temp": "Hospital/DBase.html",
                "read": department.emessage_set
                .filter(personal=False)
                .exclude(read_time=None),
                "head": str(appuser.department) + " Department's Inbox",
                "links": get_links(appuser),
            }
        else:
            queryset = {
                "unread": appuser.emessage_set.filter(read_time=None, personal = True),
                "read": appuser.emessage_set.filter(personal = True).exclude(read_time=None),
                "base_temp": "Hospital/EBase.html" if appuser.pro_level.level_number < 4 else "Hospital/SBase.html",
                "head": "{0}'s Inbox".format(appuser.app_user),
                "links": get_links(appuser),
            }

        return queryset


class Sentbox(ListView):
    model = EMessage
    template_name = "Hospital/message_list.html"

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return super(Sentbox, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        appuser = self.request.user.appuser
        department = appuser.department
        if appuser.lockdown:
            queryset = {
                "unread": department.messages_from_dept.filter(read_time=None, personal=False),
                "base_temp": "Hospital/DBase.html",
                "read": department.messages_from_dept.filter(personal=False).exclude(
                    read_time=None
                ),
                "head": str(appuser.department) + " Department's Sentbox",
                "links": get_links(appuser),
            }
        else:
            queryset = {
                "unread": appuser.sent_messages.filter(read_time=None),
                "read": appuser.sent_messages.exclude(read_time=None),
                "base_temp": "Hospital/EBase.html" if appuser.pro_level.level_number < 4 else "Hospital/SBase.html",
                "head": "{0}'s sentbox".format(appuser.app_user),
                "links": get_links(appuser),
            }
        return queryset


class Message(DetailView):
    model = EMessage
    template_name = "Hospital/message_single.html"

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated and message_possession(
            request.user, self.kwargs.get("pk")
        ):
            return super(Message, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        appuser = self.request.user.appuser
        data = super().get_context_data(**kwargs)
        msg = data["object"]
        if appuser.lockdown:
            data["base_temp"] = "Hospital/DBase.html"
        else:
            data["base_temp"] = "Hospital/EBase.html" if appuser.pro_level.level_number < 4 else "Hospital/SBase.html"

        if not msg.read_time and msg.reciever == appuser:
            msg.read_time = datetime.now()
            msg.save()
        data["links"] = get_links(self.request.user.appuser)
        return data


class NewMessagePersonal(CreateView):
    model = EMessage
    fields = ["reciever", "subject", "text"]
    template_name = "Hospital/new_message.html"

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return super(NewMessagePersonal, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        au = self.request.user.appuser
        data = super().get_context_data(**kwargs)
        data["base_temp"] = "Hospital/EBase.html" if au.pro_level.level_number < 4 else "Hospital/SBase.html"
        data["links"] = get_links(self.request.user.appuser)
        return data

    def form_valid(self, form):
        appuser = self.request.user.appuser
        msg = form.save(commit=False)
        msg.sender = appuser
        msg.personal = True
        msg.save()

        return redirect("Sentbox")


class NewMessageDepartment(CreateView):
    model = EMessage
    fields = ["reciever_dept", "subject", "text"]
    template_name = "Hospital/new_message.html"

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return super(NewMessageDepartment, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        au = self.request.user.appuser
        data = super().get_context_data(**kwargs)
        data["base_temp"] = "Hospital/DBase.html"
        data["links"] = get_links(self.request.user.appuser)
        return data

    def form_valid(self, form):
        appuser = self.request.user.appuser
        msg = form.save(commit=False)
        msg.sender_dept = appuser.department
        msg.personal = False
        msg.save()

        return redirect("Sentbox")


class MakeAnnouncement(CreateView):
    model = Announcement
    template_name = "Hospital/create.html"
    fields = ["title", "text", "target_department"]

    def dispatch(self, request, *args, **kwargs):
        if only_above(request.user, 3) or only_managers(request.user):
            return super(MakeAnnouncement, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        au = self.request.user.appuser
        data["base_temp"] = "Hospital/EBase.html" if au.pro_level.level_number < 4 else "Hospital/SBase.html"
        data["head"] = "make an announcement"
        data["links"] = get_links(au)
        return data

    def form_valid(self, form):
        obj = form.save(commit=False)

        obj.from_u = self.request.user.appuser
        obj.save()
        obj.target_department.set(form.cleaned_data.get("target_department"))
        obj.save()

        return redirect("ListAnnouncements")


class UpdateAnnouncement(UpdateView):
    model = Announcement
    template_name = "Hospital/Update.html"
    fields = ["title", "text", "target_department"]
    success_url = reverse_lazy("ListAnnouncements")

    def dispatch(self, request, *args, **kwargs):
        obj = Announcement.objects.get(pk=self.kwargs.get("pk"))
        if obj.from_u == request.user.appuser and (only_managers(request.user) or only_above(request.user, 3)):
            return super(UpdateAnnouncement, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        au = self.request.user.appuser
        data["base_temp"] = "Hospital/EBase.html" if au.pro_level.level_number < 4 else "Hospital/SBase.html"
        data["head"] = "make an announcement"
        data["links"] = get_links(au)
        return data

    def form_valid(self, form):
        d = self.request.POST.get("deletable")
        if d == "delete":
            Announcement.objects.get(pk=self.kwargs.get("pk")).delete()

        else:
            super().form_valid(form)
        return redirect("ListAnnouncements")


class ListAnnouncements(TemplateView):
    template_name = "Hospital/object_list.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return super(ListAnnouncements, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = {}
        appuser = self.request.user.appuser
        if appuser.department:
            data["old_object_list"] = appuser.department.announcement_set.all()
        data["head2"] = "Announcements concerning {0}".format(appuser.department)
        if appuser.lockdown:
            data["base_temp"] = "Hospital/DBase.html"
            data["edit_url2"] = "AnnouncementSingle"
        else:
            data["edit_url"] = "UpdateAnnouncement"
            data["edit_url2"] = "AnnouncementSingle"
            data["base_temp"] = "Hospital/EBase.html" if appuser.pro_level.level_number < 4 else "Hospital/SBase.html"
            data["object_list"] = appuser.announcement_set.all()
            data["head"] = "Your announcements"
            if appuser.is_manager() or appuser.pro_level.level_number < 4:
                data["special_link"] = ("MakeAnnouncement", "make announcement")

        data["links"] = get_links(self.request.user.appuser)
        return data


class AnnouncementSingle(DetailView):
    model = Announcement
    template_name = "Hospital/detailed_object.html"

    def dispatch(self, request, *args, **kwargs):
        obj = Announcement.objects.get(pk=self.kwargs.get("pk"))
        if  request.user.is_authenticated and request.user.appuser.department in obj.target_department.all():
            return super(AnnouncementSingle, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        au = self.request.user.appuser
        if au.lockdown:
            data["base_temp"] = "Hospital/DBase.html"
        else:
            data["base_temp"] = "Hospital/EBase.html" if au.pro_level.level_number < 4 else "Hospital/SBase.html"
        data["links"] = get_links(au)
        return data


class InventoryList(ListView):
    model = DepartmentInventory
    template_name = "Hospital/object_list.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.appuser.lockdown:
            return super(InventoryList, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        dep = self.request.user.appuser.department
        data["object_list"] = data["object_list"].filter(department=dep)
        data["base_temp"] = "Hospital/DBase.html"
        data["head"] = "Inventories of {0}".format(dep)
        data["special_link"] = ("CreateInventoryList", "Enter Items To Inventory List")
        data["edit_url"] = "ChangeInventoryList"
        data["links"] = get_links(self.request.user.appuser)
        return data


class NewInventory(CreateView):
    model = Inventory
    template_name = "Hospital/create.html"
    fields = ["item", "description"]

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.appuser.lockdown:
            return super(NewInventory, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        dep = self.request.user.appuser.department
        data = super().get_context_data(**kwargs)
        data["head"] = "new inventory"
        data["base_temp"] = "Hospital/DBase.html"
        data["links"] = get_links(self.request.user.appuser)
        return data

    def form_valid(self, form):
        nextpage = self.kwargs.get("red")
        obj = form.save(commit=False)
        obj.added_by = self.request.user.appuser
        obj.save()
        if nextpage == "Purchase":
            return redirect("CreatePurchaseList")
        else:
            return redirect("CreateInventoryList")


class InventoryCreate(FormView):
    form_class = InventoryListForm
    template_name = "Hospital/InventoryListAdd.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.appuser.lockdown:
            return super(InventoryCreate, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        dep = self.request.user.appuser.department
        data = super().get_context_data(**kwargs)
        data["base_temp"] = "Hospital/DBase.html"
        data["links"] = get_links(self.request.user.appuser)
        return data

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.department = self.request.user.appuser.department
        obj.save()
        return redirect("InventoryList")


class ChangeInventory(UpdateView):
    model = DepartmentInventory
    fields = ["count"]
    template_name = "Hospital/Update.html"
    success_url = reverse_lazy("CreateInventoryList")

    def dispatch(self, request, *args, **kwargs):
        if (
            request.user.is_authenticated
            and request.user.appuser.lockdown
            and possessing_department(request.user, self.model, self.kwargs.get("pk"))
        ):
            return super(ChangeInventory, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["base_temp"] = "Hospital/DBase.html"
        data["links"] = get_links(self.request.user.appuser)
        return data

    def form_valid(self, form):
        pk = self.kwargs["pk"]

        d = self.request.POST.get("deletable")
        if d == "delete":
            DepartmentInventory.objects.get(pk=pk).delete()
            return redirect("InventoryList")
        else:
            super().form_valid(form)

        return redirect("InventoryList")


class PurchasesList(ListView):
    model = PurchaseList
    template_name = "Hospital/object_list.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.appuser.lockdown:
            return super(PurchasesList, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        dep = self.request.user.appuser.department
        data = {
            "object_list": dep.list_to_buy.exclude(
                models.Q(closed=True) | models.Q(item_gained__gt = 0)
            ),
            "old_object_list": dep.list_to_buy.filter(models.Q(closed=True) | models.Q(item_gained__gt = 0)),
        }
        data["head"] = "purchases to be made of {0}".format(dep)
        data["head2"] = "made purchases of {0}".format(dep)
        data["base_temp"] = "Hospital/DBase.html"
        data["special_link"] = ("CreatePurchaseList", "Enter Items To Purchase List")
        data["edit_url"] = "ChangePurchaseList"
        data["links"] = get_links(self.request.user.appuser)
        return data


class Purchases(CreateView):
    model = PurchaseList
    fields = ("item", "requird_num")
    template_name = "Hospital/PurchaseListAdd.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.appuser.lockdown:
            return super(Purchases, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        dep = self.request.user.appuser.department
        data = super().get_context_data(**kwargs)
        data["links"] = get_links(self.request.user.appuser)
        data["new_inventory_form"] = InventorySubForm()
        return data

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.department = self.request.user.appuser.department
        obj.save()

        return redirect("PurchaseList")


class ChangePurchaseItem(UpdateView):
    model = PurchaseList
    fields = [
        "item",
        "requird_num",
    ]
    template_name = "Hospital/Update.html"
    success_url = reverse_lazy("PurchaseList")

    def dispatch(self, request, *args, **kwargs):
        obj = PurchaseList.objects.get(pk=self.kwargs.get("pk"))
        if (
            not obj.closed
            and obj.item_gained < 1
            and request.user.is_authenticated
            and request.user.appuser.lockdown
            and possessing_department(request.user, self.model, self.kwargs.get("pk"))
        ):
            return super(ChangePurchaseItem, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["base_temp"] = "Hospital/DBase.html"
        data["links"] = get_links(self.request.user.appuser)
        return data
    
    def form_valid(self, form):
        obj = PurchaseList.objects.get(pk = self.kwargs.get('pk'))
        if self.request.POST.get('deletable'):
            obj.delete()
        else:
            super().form_valid(form)
        return redirect("PurchaseList")


class TotalPurchaseList(ListView):
    model = PurchaseList
    template_name = "Hospital/object_list.html"

    def dispatch(self, request, *args, **kwargs):
        if only_department(request.user, "Transport"):
            return super(TotalPurchaseList, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        return {
            "object_list": PurchaseList.objects.exclude(closed=True),
            "edit_url": "EnterAquiredItems",
            "head": "List Of Purchases To be Made",
            "base_temp": "Hospital/DBase.html",
            "links": get_links(self.request.user.appuser),
        }


class OldPurchaseList(ListView):
    model = PurchaseList
    template_name = "Hospital/object_list.html"

    def dispatch(self, request, *args, **kwargs):
        if only_department(request.user, "Transport"):
            return super(OldPurchaseList, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = {
            "old_object_list": PurchaseList.objects.filter(closed = True).exclude(aquired_date__gt = (datetime.today() - timedelta(days=1))),
            "object_list" : PurchaseList.objects.filter(closed = True, aquired_date__gt = (datetime.today() - timedelta(days=1))),
            "head": "List Of Past Purchases",
            "base_temp": "Hospital/DBase.html",
            "links": get_links(self.request.user.appuser),
            "edit_url" : "EnterAquiredItems"
        }
        return data


class EnterAquiredItems(UpdateView):
    model = PurchaseList
    template_name = "Hospital/UpdateWithoutDelete.html"
    fields = ["item_gained", "total_price", "discount", "closed"]
    success_url = reverse_lazy("TotalPurchaseList")

    def dispatch(self, request, *args, **kwargs):
        obj = PurchaseList.objects.get(pk=self.kwargs.get("pk"))
        if only_department(request.user, "Transport") and (not obj.closed or not obj.aquired_date or obj.aquired_date >= (datetime.now(timezone.utc) - timedelta(days=1))):
            return super(EnterAquiredItems, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["base_temp"] = "Hospital/DBase.html"
        data["links"] = get_links(self.request.user.appuser)
        return data
    
    def form_valid(self, form):
        super().form_valid(form)
        obj = PurchaseList.objects.get(pk = self.kwargs.get('pk'))
        if obj.item_gained > 0:
            obj.aquired_date = datetime.today()
        obj.save()
        return redirect("TotalPurchaseList")


class ChangePassword(PasswordChangeView):
    template_name = "Hospital/change_pwd.html"
    success_url = reverse_lazy("PasswordChanged")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.appuser.lockdown:
            return super(ChangePassword, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["base_temp"] = "Hospital/EBase.html" if self.request.user.appuser.pro_level.level_number < 4 else "Hospital/SBase.html"
        data["links"] = get_links(self.request.user.appuser)
        return data


class PasswordChanged(TemplateView):
    template_name = "Hospital/pwd_ch_suc.html"

    def get_context_data(self, **kwargs):
        au = self.request.user.appuser
        data =  {"info": "your password is changed successfully!"}
        if au.lockdown:
            data["base_temp"] = "Hospital/DBase.html"
        else:
            data["base_temp"] = "Hospital/EBase.html" if au.pro_level.level_number < 4 else "Hospital/SBase.html"
        return data



class ChangePhoto(UpdateView):
    template_name = "Hospital/UpdateWithoutDelete.html"
    model = AppUser
    fields = ["photo"]

    def dispatch(self, request, *args, **kwargs):
        objs = AppUser.objects.filter(pk=self.kwargs.get("pk"))
        if (
            objs
            and request.user.is_authenticated
            and not request.user.appuser.lockdown
            and objs[0] == request.user.appuser
        ):
            return super(ChangePhoto, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        au = self.request.user.appuser
        if au.lockdown:
            data["base_temp"] = "Hospital/DBase.html"
        else:
            data["base_temp"] = "Hospital/EBase.html" if au.pro_level.level_number < 4 else "Hospital/SBase.html"
        data["head"] = "change profile picture"
        data["links"] = get_links(au)
        return data

    def get_success_url(self):
        if self.request.user.appuser.pro_level.level_number < 4:
            return reverse("M_ExecutiveHome")
        else:
            return reverse("SHome")


class UploadCertificate(CreateView):
    template_name = "Hospital/UpdateWithImages.html"
    model = Certificate
    fields = ["photo", "certificate_title"]

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.appuser.lockdown:
            return super(UploadCertificate, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        au = self.request.user.appuser
        certificates = au.certificate_set.all()
        data["records"] = certificates
        data["head"] = "Upload Certificates"
        data["heading"] = "Uploaded Certificates Are Shown Below"
        if au.lockdown:
            data["base_temp"] = "Hospital/DBase.html"
        else:
            data["base_temp"] = "Hospital/EBase.html" if au.pro_level.level_number < 4 else "Hospital/SBase.html"
        data["links"] = get_links(self.request.user.appuser)
        data['no_delete'] = True
        return data

    def form_valid(self, form):
        delete_image = self.request.POST.get("delete_image")
        if delete_image:
            Certificate.objects.get(pk=delete_image).delete()

        else:
            title = form.cleaned_data.get("certificate_title")
            au = self.request.user.appuser

            if not Certificate.objects.filter(staff=au, certificate_title=title):
                obj = form.save(commit=False)
                obj.staff = au
                obj.save()

        return redirect(self.request.path_info)


class ApplyLeave(CreateView):
    model = LeaveApplications
    template_name = "Hospital/apply_leave.html"
    fields = ["date", "reason"]

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.appuser.lockdown:
            return super(ApplyLeave, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        au = self.request.user.appuser
        data["head"] = "Leave Application"
        data["existing_objects"] = [[application, application.approval_possible()] for application in au.leaveapplications_set.all()]
        if au.lockdown:
            data["base_temp"] = "Hospital/DBase.html"
        else:
            data["base_temp"] = "Hospital/EBase.html" if au.pro_level.level_number < 4 else "Hospital/SBase.html"
        data["links"] = get_links(au)
        return data

    def form_valid(self, form):
        au = self.request.user.appuser
        obj = form.save(commit=False)
        obj.applicant = au
        exis_leaves = obj.applicant.leaveapplications_set.filter(date=obj.date).exclude(
            canceled=True
        )
        if not exis_leaves and obj.approval_possible():
            if au.pro_level.level_number < 4:
                obj.approved = True
            obj.save()
            return redirect(self.request.path_info)
        else:
            data = self.get_context_data(**self.kwargs)
            data[
                "error_msg"
            ] = "check date and try again, in addition are you sure you dont have any pending applications for this date? if so cancel them."
            return render(self.request, self.template_name, data)


class EditLeaveApplication(UpdateView):
    model = LeaveApplications
    template_name = "Hospital/UpdateWithoutDelete.html"
    fields = ["date", "reason", "canceled"]
    success_url = reverse_lazy("ApplyLeave")

    def dispatch(self, request, *args, **kwargs):
        obj = LeaveApplications.objects.get(pk=self.kwargs.get("pk"))
        if (
            request.user.is_authenticated
            and obj.applicant == request.user.appuser
            and obj.approval_possible()
        ):
            return super(EditLeaveApplication, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["head"] = "Leave Application"
        data["base_temp"] = "Hospital/EBase.html" if self.request.user.appuser.pro_level.level_number < 4 else "Hospital/SBase.html"
        data["links"] = get_links(self.request.user.appuser)
        return data


class ListLeaves(ListView):
    model = LeaveApplications
    template_name = "Hospital/object_list.html"

    def dispatch(self, request, *args, **kwargs):
        if only_managers(request.user):
            return super(ListLeaves, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        dep = self.request.user.appuser.department
        data["base_temp"] = "Hospital/SHome.html"
        data["head"] = "Leave Applications"
        data["edit_url"] = "ManageLeaves"

        approvables = []
        unapprovables = []
        all_leaves = (
            LeaveApplications.objects.select_related("applicant__department")
            .filter(applicant__department=dep)
            .exclude(canceled=True)
        )

        for la in all_leaves:
            if la.approval_possible():
                approvables.append(la)
            else:
                unapprovables.append(la)

        data["object_list"] = approvables
        data["old_object_list"] = unapprovables

        data["links"] = get_links(self.request.user.appuser)
        return data


class ManageLeaves(UpdateView):
    model = LeaveApplications
    fields = ["approved"]
    template_name = "Hospital/approve_leaves.html"
    success_url = reverse_lazy("ListLeaves")

    def dispatch(self, request, *args, **kwargs):
        obj = LeaveApplications.objects.get(pk=self.kwargs.get("pk"))
        if only_managers_of_department(request.user, obj.applicant.department) and obj.approval_possible() and not obj.canceled:
            return super(ManageLeaves, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["base_temp"] = "Hospital/SHome.html"
        data["head"] = "manage leave applications"
        data["links"] = get_links(self.request.user.appuser)
        return data


class ReportStaff(CreateView):
    model = StaffReport
    template_name = "Hospital/create.html"
    fields = ()

    def dispatch(self, request, *args, **kwargs):
        if only_above(request.user, 3) or only_managers(request.user):
            return super(ReportStaff, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        au = self.request.user.appuser
        data = {}

        pk = self.kwargs.get('pk')
        form = StaffReportForm(au=au)
        if pk:
            form.initial = {'staff' : form.fields['staff'].queryset.get(pk = pk)}

        data["form"] = form
        data["head"] = "Write Staff Report"
        if au.pro_level.level_number < 4:
            data["base_temp"] = "Hospital/EBase.html" 
        else:
            data["base_temp"] = "Hospital/SBase.html"
            data["links"] = get_links(au)
        return data


    def form_valid(self, form):
        au = self.request.user.appuser
        Staff = AppUser.objects.get(pk=self.request.POST.get("staff"))
        remark = self.request.POST.get("remark")
        rep = StaffReport(Staff=Staff, remark=remark, remark_by=au)
        rep.save()
        if au.pro_level.level_number < 4:
            return redirect("M_DetailStaffReport", pk  = rep.id)
        return redirect("StaffReportList")


class StaffReportList(ListView):
    model = StaffReport
    template_name = "Hospital/object_list.html"

    def dispatch(self, request, *args, **kwargs):
        if only_managers(request.user):
            return super(StaffReportList, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        dep = self.request.user.appuser.department
        return {
            "edit_url": "M_DetailStaffReport",
            "head": "Staff Reports",
            "special_link": ("ReportStaff", "Write a report"),
            "object_list": StaffReport.objects.select_related(
                "Staff__department"
            ).filter(Staff__department=dep),
            "base_temp": "Hospital/SBase.html",
            "links": get_links(self.request.user.appuser),
        }


class EditStaffReport(UpdateView):
    model = StaffReport
    template_name = "Hospital/UpdateWithoutDelete.html"
    fields = ["remark"]
    def get_success_url(self):
        if self.request.user.appuser.pro_level.level_number < 4:
            return reverse_lazy("M_DetailStaffReport", kwargs = {'pk' : self.kwargs.get('pk')})
        return reverse_lazy("StaffReportList")

    def dispatch(self, request, *args, **kwargs):
        srs = StaffReport.objects.filter(pk=self.kwargs.get("pk"))
        if (
            srs
            and not (srs[0].stop_editing or srs[0].dismissed)
            and srs[0].remark_by == request.user.appuser
            and (request.user.appuser.department == srs[0].Staff.department or request.user.appuser.pro_level.level_number < 4)
        ):
            return super(EditStaffReport, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["base_temp"] = "Hospital/EBase.html" if self.request.user.appuser.pro_level.level_number < 4 else "Hospital/SBase.html"
        data["links"] = get_links(self.request.user.appuser)
        return data


class RegisterAttendance(FormView):
    form_class = AttendanceRegistrationForm
    template_name = "Hospital/att_regstr.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.appuser.lockdown:
            return super(RegisterAttendance, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["links"] = get_links(self.request.user.appuser)
        return data

    def form_valid(self, form):
        p = self.request.POST.get("password1")
        u = form.cleaned_data.get("username")
        staff = authenticate(username=u, password=p)

        if staff:
            if staff.appuser.present():
                return render(
                    self.request,
                    self.template_name,
                    {
                        "info": "Attendance registered for {0}".format(staff),
                        "links": get_links(self.request.user.appuser),
                    },
                )
            else:
                return render(
                    self.request,
                    self.template_name,
                    {
                        "info": "You cannot register attendance if now is not your shift or you are under disciplinary action",
                        "links": get_links(self.request.user.appuser),
                    },
                )
        else:
            return render(
                self.request,
                self.template_name,
                {
                    "info": "Something went wrong check username and password",
                    "links": get_links(self.request.user.appuser),
                },
            )


class StaffAttendance(ListView):
    model = Attendance
    template_name = "Hospital/att_staff_list.html"
    queryset = Attendance.objects.all()

    def dispatch(self, request, *args, **kwargs):
        if only_managers(request.user):
            return super(StaffAttendance, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        au = self.request.user.appuser
        dep = au.department
        return {
            "present_list": dep.present_staffs(),
            "absent_list": dep.absent_staffs(),
            "leaves": dep.leaves(),
            "head": "Present Staffs [{0}]".format(Shift.current_shift()),
            "links": get_links(self.request.user.appuser),
        }


class AbsenteeReport(TemplateView):
    template_name = "Hospital/object_list.html"

    def dispatch(self, request, *args, **kwargs):
        if only_managers(request.user):
            return super(AbsenteeReport, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = {}
        department = self.request.user.appuser.department
        reports = department.get_attendances()
        attendance_reports = []
        for report in reports:
            attendance_reports.append(
                "UserName : {0},  Total days absent this year : {1},"
                "  Total days absent this month : {2}".format(
                    report[0], report[1], report[2],
                )
            )

        data["object_list"] = attendance_reports
        data["base_temp"] = "Hospital/SBase.html"
        data["head"] = "Absentee Reoprts"
        data["links"] = get_links(self.request.user.appuser)
        return data


class FileUserComplaintFeedback(CreateView):
    model = ComplaintsFeedback
    template_name = "Hospital/create.html"
    fields = [
        "concerned_department",
        "concerned_staff",
        "is_compaint",
        "on_behalf",
        "subject",
        "text",
    ]

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.appuser.lockdown:
            return super(FileUserComplaintFeedback, self).dispatch(
                request, *args, **kwargs
            )
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["head"] = "File User Complaint"
        data["base_temp"] = "Hospital/DBase.html"
        data["links"] = get_links(self.request.user.appuser)
        return data

    def form_valid(self, form):
        comp = form.save(commit=False)
        appuser = self.request.user.appuser
        comp.sender = appuser
        comp.save()
        if comp.is_compaint:
            return redirect("DHomeMsg", msg = "the complaint from {0} is submitted".format(comp.on_behalf))
        else:
            return redirect("DHomeMsg", msg = "the feedback from {0} is submitted".format(comp.on_behalf))


class FileStaffComplaintFeedback(CreateView):
    model = ComplaintsFeedback
    template_name = "Hospital/create.html"
    fields = [
        "concerned_department",
        "concerned_staff",
        "is_compaint",
        "subject",
        "text",
    ]

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.appuser.lockdown:
            return super(FileStaffComplaintFeedback, self).dispatch(
                request, *args, **kwargs
            )
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["head"] = "File Staff Complaint"
        data["base_temp"] = "Hospital/SBase.html"
        data["links"] = get_links(self.request.user.appuser)
        return data

    def form_valid(self, form):
        comp = form.save(commit=False)
        appuser = self.request.user.appuser
        comp.is_complaint = True
        comp.sender = appuser
        comp.save()
        return redirect("ListComplaints")


class ListComplaints(ListView):
    model = ComplaintsFeedback
    template_name = "Hospital/object_list.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.appuser.lockdown:
            return super(ListComplaints, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        au = self.request.user.appuser
        data = {
            "edit_url": "ComplaintsInDetail",
            "base_temp": "Hospital/SBase.html",
            "head": "Complaints and Feedbacks",
            "links": get_links(self.request.user.appuser),
        }

        if au.is_manager():
            data["head"] = "complaints/feedback concerning {0} department".format(
                au.department
            )
            data["object_list"] = au.department.complaintsfeedback_set.order_by("concluded")
            data["edit_url"] = "ComplaintsInDetail"

        data["special_link"] = ("FileStaffComplaintFeedback", "new complaint/feedback")
        data["base_temp"] = "Hospital/SBase.html"
        data["old_object_list"] = au.complaintsfeedback_set.filter(on_behalf = None)
        data["head2"] = "your complaints/feedback"
        data["link"] = get_links(au)
        data["edit_url2"] = "ChangeComplaint"

        return data


class ChangeComplaint(UpdateView):
    model = ComplaintsFeedback
    template_name = "Hospital/Update.html"
    fields = ["concluded", "subject", "concerned_department", "concerned_staff", "text"]
    success_url = "ListComplaints"

    def dispatch(self, request, *args, **kwargs):
        obj = ComplaintsFeedback.objects.get(pk=self.kwargs.get("pk"))
        if (
            not request.user.appuser.lockdown
            and obj.sender == request.user.appuser
            and not obj.on_behalf
        ) or (obj.on_behalf and request.user.appuser.lockdown):
            return super(ChangeComplaint, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.user.appuser.lockdown:
            data["base_temp"] = "Hospital/DBase.html"
        else:
            data["base_temp"] = "Hospital/SBase.html"

        data["head"] = "update complaints/feedback"
        data["links"] = get_links(self.request.user.appuser)
        return data

    def form_valid(self, form):
        pk = self.kwargs["pk"]
        d = self.request.POST.get("deletable")
        if d == "delete":
            ComplaintsFeedback.objects.get(pk=pk).delete()
        else:
            super().form_valid(form)

        return redirect("ListComplaints")


class ComplaintsInDetail(UpdateView):
    model = ComplaintsFeedback
    fields = ["concluded"]
    template_name = "Hospital/detail.html"

    def get_success_url(self):
        complaint = ComplaintsFeedback.objects.get(pk = self.kwargs.get('pk'))
        if self.request.user.appuser.pro_level.level_number < 4:
            return reverse_lazy("M_DepartmentalComplaints", kwargs = {'pk' : complaint.concerned_department.id})
        else:
            return reverse_lazy("ListComplaints")

    def dispatch(self, request, *args, **kwargs):
        obj = ComplaintsFeedback.objects.get(pk=self.kwargs.get("pk"))
        if only_managers_of_department(
            request.user, obj.concerned_department
        ) or only_above(request.user, 3):
            return super(ComplaintsInDetail, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["links"] = get_links(self.request.user.appuser)
        data["base_temp"] = "Hospital/EBase.html" if self.request.user.appuser.pro_level.level_number < 4 else 'Hospital/SBase.html'
        return data
    
    def form_valid(self, form):
        super().form_valid(form)
        obj = ComplaintsFeedback.objects.get(pk = self.kwargs.get('pk'))
        auth_remark = self.request.POST.get("auth_remark")
        if auth_remark:
            obj.authority_remark = auth_remark
            obj.save()
        return redirect(self.get_success_url())


@receiver(user_logged_out)
def clear_lockdown_logged_out(sender, user, request, **kwargs):
    try:
        user.appuser.lockdown = False
        user.appuser.save()
    except:
        pass


class UpdatePersonalDetails(UpdateView):
    model = AppUser
    template_name = "Hospital/signup.html"
    fields = ("phone", "qualifications")

    def get_success_url(self):
        return reverse_lazy("UpdatePersonalDetails", kwargs={"pk": self.kwargs["pk"]})

    def dispatch(self, request, *args, **kwargs):
        if (
            self.request.user.is_authenticated
            and not self.request.user.appuser.lockdown
            and self.request.user.appuser.pk == self.kwargs.get("pk")
        ):
            return super(UpdatePersonalDetails, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        init_values_addr = model_to_dict(data["object"].address)
        init_values_au = model_to_dict(data["object"].app_user)
        data["sub_form"] = ChangeUserDetailsForm(initial=init_values_au)
        data["sub_form_addr"] = AddressForm(initial=init_values_addr)
        data["base_temp"] = "Hospital/EBase.html" if data['object'].pro_level.level_number < 4 else "Hospital/SBase.html"
        data["head"] = "Update Personal Details of {0}".format(data["object"].app_user)
        data["links"] = get_links(self.request.user.appuser)
        return data

    def form_valid(self, form):
        values = self.request.POST
        obj = self.request.user.appuser.address
        obj.place = values.get("place")
        obj.zip_code = values.get("zip_code")
        obj.district = District.objects.get(pk=values.get("district"))
        obj.save()

        user = self.request.user
        user.first_name = values.get("first_name")
        user.last_name = values.get("last_name")
        user.email = values.get("email")
        user.save()

        super().form_valid(form)
        data = self.get_context_data(**self.kwargs)
        data['su_msg'] = 'Changes successfully made! :)'
        return render(self.request, self.template_name, data)


class AllStaffs(TemplateView):
    template_name = "Hospital/object_list.html"

    def dispatch(self, request, *args, **kwargs):
        if only_managers(request.user):
            return super(AllStaffs, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = {}
        department = self.request.user.appuser.department
        staffs = department.appuser_set.all()
        data["base_temp"] = "Hospital/SBase.html"

        data["head"] = "Staffs of {0} department".format(
            self.request.user.appuser.department
        )
        data["object_list"] = staffs
        data["edit_url"] = "ChangeShiftDep"
        data["links"] = get_links(self.request.user.appuser)

        data["old_object_list"] = DisciplinaryAction.objects.select_related(
            "person__department"
        ).filter(person__department=department).exclude(is_complete = True)
        data["head2"] = "staffs under desciplinary actions"
        data["edit_url2"] = "ActionDetails"

        return data


class ActionDetails(UpdateView):
    model = DisciplinaryAction
    fields = ["is_complete"]
    template_name = "Hospital/ActionDetails.html"

    def dispatch(self, request, *args, **kwargs):
        obj = DisciplinaryAction.objects.get(pk = self.kwargs.get("pk"))
        if only_above(request.user, 3) or (not obj.is_dismissal and only_managers(request.user)):
            return super(ActionDetails, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_success_url(self):
        return reverse_lazy("ActionDetails", kwargs = {'pk' : self.kwargs.get('pk')})

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        au = self.request.user.appuser
        if au.pro_level.level_number < 4:
            data['base_temp'] = "Hospital/EBase.html"
            data['editable'] = False if (data['object'].is_complete and (not data['object'].end_date or data['object'].end_date.date() <= datetime.today().date() - timedelta(days=2))) else True
        else:
            data['base_temp'] = "Hospital/SBase.html"
            data["links"] = get_links(au)
            data['mark_completion'] = ((not data['object'].is_complete and data['object'].end_date.date() <= datetime.today().date())
            or (data['object'].is_complete and data['object'].end_date.date() >= datetime.today().date() - timedelta(days=2)))
        return data
    
    def form_valid(self, form):
        act = DisciplinaryAction.objects.get(pk = self.kwargs.get('pk'))
        dis = act.is_dismissal
        super().form_valid(form)
        act.refresh_from_db()
        if dis and act.is_complete:
            return redirect("ChangeShiftDep", pk = act.person.id)
        else:
            return redirect("ActionDetails", pk= self.kwargs.get('pk'))




class ChangeShiftDep(UpdateView):
    model = AppUser
    template_name = "Hospital/UpdateWithoutDelete.html"
    fields = ["department", "shift"]
    def get_success_url(self):
        if self.request.user.appuser.pro_level.level_number < 4:
            return reverse_lazy("M_StaffWithoutShift")
        return reverse_lazy("AllStaffs")

    def dispatch(self, request, *args, **kwargs):
        dep = AppUser.objects.get(pk=self.kwargs.get("pk")).department
        if only_managers_of_department(request.user, dep) or only_above(request.user, 3):
            return super(ChangeShiftDep, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['base_temp'] = "Hospital/EBase.html" if self.request.user.appuser.pro_level.level_number < 4 else "Hospital/SBase.html"
        data["head"] = "Change Shift and Department of {0}".format(
            data["object"].app_user
        )
        data["links"] = get_links(self.request.user.appuser)
        return data


class TheDeparted(TemplateView):
    template_name = "Hospital/departed.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return super(TheDeparted, self).dispatch(
                request, *args, **kwargs
            )
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["links"] = get_links(self.request.user.appuser)
        if not self.request.user.appuser.lockdown and self.request.user.appuser.check_profession(4):
            data['doc'] = 'doc'
        data["base_temp"] = "Hospital/DBase.html" if self.request.user.appuser.lockdown else "Hospital/SBase.html"
        return data


class FatalityReportsList(TemplateView):
    template_name = "Hospital/object_list.html"

    def dispatch(self, request, *args, **kwargs):
        if not only_departments(request.user, ['Transport', 'RoomService']):
            return super(FatalityReportsList, self).dispatch(
                request, *args, **kwargs
            )
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = {}
        data["base_temp"] = "Hospital/DBase.html" if self.request.user.appuser.lockdown else "Hospital/SBase.html"
        data["links"] = get_links(self.request.user.appuser)
        data["object_list"] = Fatality.objects.all()
        if only_medical(self.request.user):
            data["edit_url"] = "FatalityReport"
        data['head'] = 'fatalities'
        return data


class ReportFatality(FormView):
    form_class = FatalityForm
    template_name = "Hospital/FReport.html"

    def dispatch(self, request, *args, **kwargs):
        if only_doctors(request.user):
            return super(ReportFatality, self).dispatch(
                request, *args, **kwargs
            )
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        new_patient = self.kwargs.get("patient")

        data["deceased_comp_form"] = DeceasedCompanionForm()
        if self.kwargs.get("unidentified") == "patient_unknown":
            data["unknown_patients"] = PatientUnknown.objects.filter(deceased=False)
        else:
            data["patients"] = PatientPersonalReccord.objects.filter(deceased=False)

        data["links"] = get_links(self.request.user.appuser)
        data["accidents"] = Accident.objects.all()
        return data

    def form_valid(self, form):
        aut = self.request.POST.get("autopsy")
        hr_obj = DeceasedCompanionForm(self.request.POST)
        if not hr_obj.is_valid():
            raise Http404

        p_id = self.request.POST.get("patient")
        up_id = self.request.POST.get("patient_unknown")

        if p_id:
            pat = PatientPersonalReccord.objects.get(pk=p_id)
        elif up_id:
            pat = PatientUnknown.objects.get(pk=up_id)

        hr = pat.get_active_health_reccord()

        if not hr:
            hr = PatientHealthReccord(patient=pat) if p_id else PatientHealthReccord(patient_unknown=pat, patient = None)
            hr.op_time_stamp = datetime.now()
            hr.save()

        if hr_obj.cleaned_data.get('companion_name'):
            hr.companion_name = hr_obj.cleaned_data.get('companion_name')
        if hr_obj.cleaned_data.get('companion_phone'):
            hr.companion_phone = hr_obj.cleaned_data.get('companion_phone')
        if hr_obj.cleaned_data.get('accident'):
            hr.accident = hr_obj.cleaned_data.get('accident')
        hr.save()

        deceased = Fatality(
            date_of=form.cleaned_data.get("date_of"),
            time_of=form.cleaned_data.get("time_of"),
            cause = form.cleaned_data.get('cause'),
            hr=hr,
            cause_description = form.cleaned_data.get('cause_description'),
            death_report = form.cleaned_data.get('death_report'),
            updated_by = self.request.user.appuser
        )
        deceased.save()
        pat.deceased = True
        pat.save()

        obj = hr.admission_set.exclude(ad_time=None).filter(dis_time=None)
        if obj:
            hr.discharge(obj[0])
        else:
            hr.discharge(None)
        hr.admission_set.exclude(ad_time=None).delete()

        hr.status_code = -1
        hr.save()
        if aut == "mark":
            aut_obj = Surgery(
                record=hr, surgery_name="Autopsy", organ_under_surgery=None, is_autopsy = True,
                surgery_report = 'autopsy not completed', initiated_by = self.request.user.appuser
            )
            aut_obj.save()
            deceased.autopsy = aut_obj
            deceased.save()
            return redirect("SurgeryForm", pk=aut_obj.pk)

        return redirect("FatalityReport", pk=deceased.id)


class FatalityReport(TemplateView):
    template_name = "Hospital/fatality_report.html"

    def dispatch(self, request, *args, **kwargs):
        if only_medical(request.user):
            return super(FatalityReport, self).dispatch(
                request, *args, **kwargs
            )
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        u = self.request.user
        pk = self.kwargs.get("pk")
        death_report = Fatality.objects.get(pk=pk)
        if death_report.autopsy:
            control = 1 if surgery_key_control(u, death_report.autopsy) else (2 if surgery_info_control(u, death_report.autopsy) else 3)
        else:
            control = 1 if only_doctors_and_departments(u, [death_report.updated_by.department.department_name]) else (2 if u.appuser.check_profession(5) else 3)
        data = {
            "hr" : death_report.hr,
            "autopsy": death_report.autopsy,
            "death_report": death_report,
            "control" : control,
            "base_temp" : 'Hospital/DBase.html' if u.appuser.lockdown else 'Hospital/SBase.html',
            "links" : get_links(u.appuser),
            "uploaded_files": death_report.autopsy.surgerydocuments_set.all() if death_report.autopsy else []
        }
        data["patient"] = death_report.hr.patient_unknown if death_report.hr.patient_unknown else death_report.hr.patient
        if death_report.hr.patient_unknown:
            data['unknown'] = 'unknown'
        return data


class WriteFatalityReport(UpdateView):
    model = Fatality
    template_name = "Hospital/write_autopsy_report.html"
    fields = ["date_of", "time_of", "cause", "cause_description", "death_report"]

    def dispatch(self, request, *args, **kwargs):
        obj = Fatality.objects.get(pk = self.kwargs.get('pk'))
        if (obj.autopsy and surgery_key_control(request.user, obj.autopsy)) or( not obj.autopsy and only_doctors_and_departments(request.user, [obj.updated_by.department.department_name])):
            return super(WriteFatalityReport, self).dispatch(
                request, *args, **kwargs
            )
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_success_url(self):
        return reverse_lazy("FatalityReport", kwargs={"pk": self.kwargs.get("pk")})

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        autopsy = data["object"].autopsy
        if autopsy:
            data["sub_form"] = SurgeryWritingForm(
                initial={
                    "end_date": autopsy.end_date,
                    "end_time": autopsy.end_time,
                    "surgery_report": autopsy.surgery_report,
                }
            )

        data["accidents"] = Accident.objects.all()
        data["patient"] = data["object"].hr.patient
        if data["object"].hr.patient_unknown:
            data["patient_unknown"] = data["object"].hr.patient_unknown
        data["links"] = get_links(self.request.user.appuser)
        data["selected_acc"] = data["object"].hr.accident
        return data

    def form_valid(self, form):
        acc_id = self.request.POST.get("accident")
        fatality = Fatality.objects.get(pk=self.kwargs.get("pk"))
        hr = fatality.hr

        dele = self.request.POST.get('deletebale')
        if dele == 'delete_now':
            if fatality.autopsy:
                if not fatality.autopsy.end_time:
                    fatality.autopsy.deduct_from_bill()
                fatality.autopsy.delete()

            fatality.delete()
            if hr.patient:
                hr.patient.deceased = False
                hr.patient.save()
            elif hr.patient_unknown:
                hr.patient_unknown.deceased = False
                hr.patient_unknown.save()
            hr.status_code = 5
            hr.save()
            return redirect("FatalityReportsList")

        sur_form = SurgeryWritingForm(self.request.POST)
        if sur_form.is_valid():
            autopsy = fatality.autopsy
            autopsy.end_date = sur_form.cleaned_data.get("end_date")
            autopsy.end_time = sur_form.cleaned_data.get("end_time")
            autopsy.surgery_report = sur_form.cleaned_data.get("surgery_report")
            autopsy.save()

        if acc_id:
            accident = Accident.objects.get(pk=acc_id)
            hr.accident = accident
        else:
            hr.accident = None
        hr.save()

        super().form_valid(form)

        fatality.refresh_from_db()
        fatality.updated_by = self.request.user.appuser
        fatality.save()

        new_auto = self.request.POST.get('autopsy')
        if not fatality.autopsy and new_auto == 'mark':
            sur =  Surgery(
                record=hr, surgery_name="Autopsy", organ_under_surgery=None, is_autopsy = True,
                surgery_report = 'autopsy not completed', initiated_by = self.request.user.appuser)
            sur.save()
            fatality.autopsy = sur
            fatality.save()
            s = fatality.autopsy
        if hr.patient:
            hr.patient.deceased = True
            hr.patient.save()

        return redirect("FatalityReport", pk=self.kwargs.get("pk"))


class AutopsyList(TemplateView):
    template_name = "Hospital/object_list.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return super(AutopsyList, self).dispatch(
                request, *args, **kwargs
            )
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = {}
        data['object_list'] = Fatality.objects.filter(autopsy__in = Surgery.objects.filter(is_autopsy = True, end_date = None))
        data['base_temp'] = "Hospital/DBase.html" if self.request.user.appuser.lockdown else "Hospital/SBase.html"
        data['head'] = 'autopsies yet to complete'
        if only_medical(self.request.user):
            data['edit_url'] = data['edit_url2'] = 'FatalityReport'
        data['head2'] = 'autopsies completed'
        data['old_object_list'] = Fatality.objects.filter(autopsy__in = Surgery.objects.filter(is_autopsy = True).exclude(end_date = None))
        data['links'] = get_links(self.request.user.appuser)
        return data


class MorgueList(TemplateView):
    template_name = "Hospital/object_list.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return super(MorgueList, self).dispatch(
                request, *args, **kwargs
            )
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["base_temp"] = "Hospital/DBase.html" if self.request.user.appuser.lockdown else "Hospital/SBase.html"
        data['object_list'] = Morgue.objects.exclude(dismissed = True)
        data['head'] = 'active'
        data['old_object_list'] = ["{0} ({1} : {2}h to {3} : {4}h) amount : {5}".format(m, m.start_date, m.start_time.hour, m.end_date, m.end_time.hour, m.amnt) for m in Morgue.objects.filter(dismissed = True)]
        data['head2'] = 'inactive'
        data['links'] = get_links(self.request.user.appuser)
        if self.request.user.appuser.check_department('Morgue'):
            data['special_link'] = ('CreateMorgue', 'create new entry')
            data['edit_url'] =  'EditMorgue'
        return data


class CreateMorgue(CreateView):
    model = Morgue
    fields = ['patient', 'door_no', 'only_morgue_service']
    template_name = 'Hospital/Create.html'

    success_url = reverse_lazy("MorgueList")
    def dispatch(self, request, *args, **kwargs):
        if only_department(request.user, 'Morgue'):
            return super(CreateMorgue, self).dispatch(
                request, *args, **kwargs
            )
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['base_temp'] = "Hospital/DBase.html"
        data['head'] = "morgue entry"
        data['links'] = get_links(self.request.user.appuser)
        return data


class EditMorgue(UpdateView):
    model = Morgue
    fields = ['patient', 'door_no', 'dismissed', 'amnt', 'only_morgue_service']
    template_name = 'Hospital/UpdateWithoutDelete.html'

    success_url = reverse_lazy("MorgueList")
    def dispatch(self, request, *args, **kwargs):
        if only_departments(request.user, ['Morgue']):
            return super(EditMorgue, self).dispatch(
                request, *args, **kwargs
            )
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['base_temp'] = "Hospital/DBase.html"
        data['head'] = "change morgue details"
        data['links'] = get_links(self.request.user.appuser)
        data["extra_info"] = "admitted @ {0} on {1}".format(data['object'].start_time, data['object'].start_date)
        return data

    def form_valid(self, form):
        morg = Morgue.objects.get(pk = self.kwargs.get('pk'))
        super().form_valid(form)

        if form.cleaned_data.get('dismissed'):
            morg = form.save(commit = False)
            morg.end_date = datetime.today()
            morg.end_time = datetime.now()
            morg.save()
        
        return redirect('MorgueList')


class AddHumanOrgans(FormView):
    form_class = HumanOrganForm
    template_name = "Hospital/create.html"

    def dispatch(self, request, *args, **kwargs):
        if only_medical_departments(request.user):
            return super(AddHumanOrgans, self).dispatch(
                request, *args, **kwargs
            )
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['links'] = get_links(self.request.user.appuser)
        data['base_temp'] = "Hospital/DBase.html"
        data['head'] = 'Human organ'
        return data

    def form_valid(self, form):
        organ_class = self.request.POST.get('organ_class')
        obj = form.save(commit = False)
        obj.organ_class = organ_class
        obj.save()
        obj.related_organs.set(form.cleaned_data.get('related_organs'))
        return redirect('DetailsOrgan', pk = obj.pk)


class ListOrgans(TemplateView):
    template_name = 'Hospital/object_list.html'

    def dispatch(self, request, *args, **kwargs):
        if only_medical_departments(request.user):
            return super(ListOrgans, self).dispatch(
                request, *args, **kwargs
            )
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = {'object_list' : HumanOrgan.objects.all()}
        data['links'] = get_links(self.request.user.appuser)
        data['head'] = 'human organs'
        data['edit_url'] = 'DetailsOrgan'
        data['base_temp'] = 'Hospital/DBase.html'
        data['special_link'] = ('AddHumanOrgans', 'new')
        return data


class UpdateOrgan(FormView):
    form_class = HumanOrganForm
    template_name = "Hospital/UpdateWithImages.html"
    fields = ['organ_name', 'organ_description', 'photo', 'related_organs']

    def dispatch(self, request, *args, **kwargs):
        if only_medical_departments(request.user):
            return super(UpdateOrgan, self).dispatch(
                request, *args, **kwargs
            )
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['object'] = HumanOrgan.objects.get(pk = self.kwargs.get('pk'))
        data['links'] = get_links(self.request.user.appuser)
        data['head'] = "update organ"
        data['records'] = [data['object']]
        data["form"].initial = model_to_dict(data['object'])
        data['base_temp'] = 'Hospital/DBase.html'
        return data

    def form_valid(self, form):
        delete_image = self.request.POST.get("delete_image")
        deleteable = self.request.POST.get("deletable")
        if delete_image:
            HumanOrgan.objects.filter(pk=self.kwargs.get('pk')).update(photo = None)
            return redirect('DetailsOrgan', pk = self.kwargs.get('pk'))
        elif deleteable:
            HumanOrgan.objects.filter(pk=self.kwargs.get('pk')).delete()
            return redirect('ListOrgans')
        else:
            obj = form.save(commit = False)
            organ_class = self.request.POST.get('organ_class')
            cur_organ = HumanOrgan.objects.get(pk = self.kwargs.get('pk'))

            if not obj.photo:
                obj.photo = cur_organ.photo
            obj.organ_class = organ_class
            obj.id = self.kwargs.get('pk')
            obj.save()
            obj.related_organs.set(form.cleaned_data.get('related_organs'))
            obj.save()

            return redirect('DetailsOrgan', pk = self.kwargs.get('pk'))


def remove_dupes(liz):
    new_liz = []
    for item in liz:
        if item not in new_liz:
            new_liz.append(item)

    return new_liz


class DetailsOrgan(TemplateView):
    template_name = 'Hospital/HumanOrganDetails.html'

    def dispatch(self, request, *args, **kwargs):
        if only_medical_departments(request.user):
            return super(DetailsOrgan, self).dispatch(
                request, *args, **kwargs
            )
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = {'object' : HumanOrgan.objects.get(pk = self.kwargs.get('pk'))}
        data['links'] = get_links(self.request.user.appuser)
        data['related_images'] = data['object'].related_organs.all() | data['object'].humanorgan_set.all()
        data['related_images'] = remove_dupes(data['related_images'])
        return data


#-------------------------------------------------------------------------------------------------
# views for executive staffs
#-------------------------------------------------------------------------------------------------

class M_SalaryManagement(ListView):
    template_name = "Hospital/LevelSalary.html"
    queryset = Level.objects.all()

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_superuser or only_above(request.user, 3):
            return super(M_SalaryManagement, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("M_ExecutiveHome", "Go Home")}
            )

class M_ChangeBasicSalary(UpdateView):
    model = Level
    fields = ['base_salary']
    template_name = "Hospital/UpdateWithoutDelete.html"
    success_url = reverse_lazy("M_SalaryManagement")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_superuser or only_above(request.user, 3):
            return super(M_ChangeBasicSalary, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("M_ExecutiveHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['base_temp'] = "Hospital/EBase.html"
        data['head'] = 'basic salary of {0}'.format(data['object'])
        return data

class M_StaffOfLevel(TemplateView):
    template_name = "Hospital/LevelStaffSalary.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_superuser or only_above(request.user, 3):
            return super(M_StaffOfLevel, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("M_ExecutiveHome", "Go Home")}
            )
    
    def get_context_data(self, **kwargs):
        dep = self.request.GET.get('department')
        level = Level.objects.get(pk = self.kwargs.get('pk'))
        salaries = Salary.objects.select_related("staff__pro_level").filter(staff__pro_level = level)
        selected_dep = []
        if dep:
            selected_dep = [dep, 'all departments']
            department = Department.objects.filter(pk = dep)
            if department:
                salaries = salaries.select_related('staff__department').filter(staff__department = department[0])
                selected_dep[1] = department[0].department_name

        return {'object_list' : salaries, 'departments' : Department.objects.all(), 'selected_dep' : selected_dep}


class M_IndividualSalary(DetailView):
    model = Salary
    template_name = "Hospital/IndividualSalary.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_superuser or only_above(request.user, 3):
            return super(M_IndividualSalary, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("M_ExecutiveHome", "Go Home")}
            )


class M_ChangeIndividualSalary(UpdateView):
    model = Salary
    fields = ['bonus', 'exp_increment', 'other_increment']
    template_name = "Hospital/UpdateWithoutDelete.html"
    def get_success_url(self):
        return reverse_lazy("M_IndividualSalary", kwargs = {'pk' : self.kwargs.get('pk')})

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_superuser or only_above(request.user, 3):
            return super(M_ChangeIndividualSalary, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("M_ExecutiveHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['base_temp'] = "Hospital/EBase.html"
        data['head'] = 'salary of {0}'.format(data['object'].staff)
        return data


class M_RegisterSuperintendent(CreateView):
    model = AppUser
    fields = ['phone', 'qualifications', 'pro_level']
    template_name = "Hospital/superintend_register.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_superuser or only_above(request.user, 3):
            return super(M_RegisterSuperintendent, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("M_ExecutiveHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['user_form'] = SignUpForm()
        data['address_form'] = AddressForm()
        data['form'].fields['pro_level'].queryset = Level.objects.filter(level_number__lt = 4)
        if not self.request.user.is_superuser:
            data["base_temp"] = "Hospital/EBase.html"
            data['links'] = get_links(self.request.user.appuser)
        else:
            data["base_temp"] = "Hospital/base.html"
        return data

    def form_valid(self, form):
        user_form = SignUpForm(self.request.POST, self.request.FILES)
        address_form = AddressForm(self.request.POST)

        if user_form.is_valid():
            user_form.save()
            username = user_form.cleaned_data.get("username")
            raw_password = user_form.cleaned_data.get("password1")
            user = authenticate(username=username, password=raw_password)
            login(self.request, user)

            qs = form.cleaned_data.get("qualifications")
            if address_form.is_valid():
                ad = address_form.save(commit=False)
                ad.save()

                appuser = form.save(commit = False)
                appuser.app_user = user
                appuser.address = ad
                appuser.save()
                appuser.qualifications.set(qs)
                appuser.save()
                Salary.objects.get_or_create(staff=appuser)

        return redirect("SelectPage")


class M_ExecutiveHome(TemplateView):
    template_name = "Hospital/ExecutiveHome.html"

    def dispatch(self, request, *args, **kwargs):
        if only_above(request.user, 3):
            return super(M_ExecutiveHome, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = {}
        executives = Level.objects.filter(level_number__lt = 4)
        data["e_men"] = AppUser.objects.filter(pro_level__in = executives)
        data["notifications"] = manage_notifications(self.request.user.appuser, False)
        return data


class M_NewDisciplinaryAction(CreateView):
    model = DisciplinaryAction
    fields = ["person", "fine", "start_date", "end_date", "is_dismissal", "reason"]
    template_name = "Hospital/Create.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_superuser or only_above(request.user, 3):
            return super(M_NewDisciplinaryAction, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("M_ExecutiveHome", "Go Home")}
            )
    
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["form"].fields["person"].queryset = AppUser.objects.filter(pro_level__level_number__gt = 3)
        data['base_temp'] = "Hospital/EBase.html"
        data['head'] = "new disciplinary actions"
        return data
    
    def form_valid(self, form):
        obj = form.save(commit = False)
        if not obj.is_dismissal and not obj.end_date:
            data = self.get_context_data(**self.kwargs)
            data['error_msg'] = "if not dissmissal end date is mandatory."
            return render(self.request, self.template_name, data)
        else:
            obj.save()
        return redirect("M_AllDisciplinaryActions")


class M_AllDisciplinaryActions(TemplateView):
    template_name = "Hospital/AllDisciplinaryActions.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_superuser or only_above(request.user, 3):
            return super(M_AllDisciplinaryActions, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("M_ExecutiveHome", "Go Home")}
            )
    
    def get_context_data(self, **kwargs):
        dep = self.request.GET.get('department')
        actions = DisciplinaryAction.objects.order_by('is_complete')
        selected_dep = []
        if dep:
            selected_dep = [dep, 'all departments']
            department = Department.objects.filter(pk = dep)
            if department:
                actions = actions.select_related('person__department').filter(person__department = department[0]).order_by('issued_date')
                selected_dep[1] = department[0].department_name

        return {'object_list' : actions, 'departments' : Department.objects.all(), 'selected_dep' : selected_dep}


class M_ChangeDisciplinaryAction(UpdateView):
    model = DisciplinaryAction
    fields = ["start_date","fine", "end_date", "is_dismissal", "reason", "is_complete"]
    template_name = "Hospital/UpdateWithoutDelete.html"

    def dispatch(self, request, *args, **kwargs):
        if only_above_prof(request.user, 3):
            return super(M_ChangeDisciplinaryAction, self).dispatch(
                request, *args, **kwargs
            )
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_success_url(self):
        return reverse_lazy("ActionDetails", kwargs = {"pk": self.kwargs.get('pk')})

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['base_temp'] = "Hospital/EBase.html"
        data['head'] = "disciplinary action againts {0}".format(data['object'].person.app_user)
        return data

class M_StaffReports(TemplateView):
    template_name = "Hospital/object_list.html"

    def dispatch(self, request, *args, **kwargs):
        if only_above(request.user, 3):
            return super(M_StaffReports, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        staff = AppUser.objects.get(pk=self.kwargs.get("pk"))
        res = staff.staffreport_set.filter(Staff=staff).order_by("filed_date").reverse()
        data = {
            "object_list": res,
            "links": get_links(self.request.user.appuser),
            "head": "reports of {0}".format(staff.app_user),
            "edit_url": "M_DetailStaffReport",
            "base_temp": "Hospital/EBase.html",
            "special_link2": (
                "/Hospital/management/m_detail_staff_statistics/{0}".format(staff.id),
                "{0}'s statistics".format(staff.app_user),
            ),
        }

        return data


class M_Staffs(TemplateView):
    template_name = "Hospital/staffs_list.html"

    def dispatch(self, request, *args, **kwargs):
        if only_above(request.user, 3):
            return super(M_Staffs, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        dep = Department.objects.get(pk=self.kwargs.get("pk"))
        reps = dep.appuser_set.all()

        return {
            "object_list": reps,
            "links": get_links(self.request.user.appuser),
            "head": "staffs of {0} department".format(dep),
            "edit_url": "M_StaffReports",
            "base_temp": "Hospital/EBase.html",
        }


class M_StaffPerformances(TemplateView):
    template_name = "Hospital/object_list.html"

    def dispatch(self, request, *args, **kwargs):
        if only_above(request.user, 3):
            return super(M_StaffPerformances, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        dep = Department.objects.get(pk=self.kwargs.get("pk"))
        aus = dep.appuser_set.all()

        return {
            "object_list": aus,
            "links": get_links(self.request.user.appuser),
            "edit_url": "M_DetailStaffStatistics",
            "base_temp": "Hospital/EBase.html",
            "head": "performance statistics - department of {0}".format(dep),
        }


class M_PersonalComplaints(ListView):
    model = ComplaintsFeedback
    template_name = "Hospital/object_list.html"

    def dispatch(self, request, *args, **kwargs):
        staff = AppUser.objects.get(pk=self.kwargs.get("pk"))
        man = only_managers_of_department(request.user, staff.department)
        if only_above(request.user, 3) or man:
            return super(M_PersonalComplaints, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        staff = AppUser.objects.get(pk=self.kwargs.get("pk"))
        data = {
            "object_list": staff.complaints_concerned.exclude(
                concerned_staff=None
            ).order_by("concerned_staff")
        }
        data["links"] = get_links(self.request.user.appuser)
        data['base_temp'] = "Hospital/EBase.html" if self.request.user.appuser.pro_level.level_number < 4 else "Hospital/SBase.html"
        data["edit_url"] = "ComplaintsInDetail"
        data["head"] = "complaints/feedbacks concerning {0}".format(staff.app_user)
        return data


class M_DepartmentalComplaints(ListView):
    model = ComplaintsFeedback
    template_name = "Hospital/object_list.html"

    def dispatch(self, request, *args, **kwargs):
        if only_above(request.user, 3):
            return super(M_DepartmentalComplaints, self).dispatch(
                request, *args, **kwargs
            )
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        dep = Department.objects.get(pk=self.kwargs.get("pk"))
        data = {
            "object_list": dep.complaintsfeedback_set.all()
            .order_by("time_filed")
            .reverse()
        }
        data["links"] = get_links(self.request.user.appuser)
        data["base_temp"] = "Hospital/EBase.html"
        data["edit_url"] = "ComplaintsInDetail"
        data["head"] = "complaints/feedback against {0}".format(dep)
        return data


class M_Departments(TemplateView):
    template_name = "Hospital/AllDepartments.html"

    def dispatch(self, request, *args, **kwargs):
        if only_above(request.user, 3):
            return super(M_Departments, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = {"object_list": Department.objects.all()}
        data["base_temp"] = "Hospital/EBase.html"
        data["head"] = "departments"
        data["edit_url"] = "M_DepartmentReport"
        return data


class M_DepartmentStatsList(TemplateView):
    template_name = "Hospital/object_list.html"

    def dispatch(self, request, *args, **kwargs):
        if only_above(request.user, 3):
            return super(M_DepartmentStatsList, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = {"object_list": Department.objects.filter(is_medical = True)}
        data["base_temp"] = "Hospital/EBase.html"
        data["head"] = "department wise stats"
        data["edit_url"] = "M_DepartmentStatistics"
        return data


class M_DepartmentReport(TemplateView):
    template_name = "Hospital/DepartmentReport.html"

    def dispatch(self, request, *args, **kwargs):
        if only_above(request.user, 3):
            return super(M_DepartmentReport, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = {}
        dep = Department.objects.get(pk=self.kwargs.get("pk"))
        data["department"] = dep
        data["managers"] = list(data["department"].departmentmanager_set.all())
        data["staffs_no"] = dep.appuser_set.count()
        data["doc_no"] = (
            dep.appuser_set.select_related("pro_level__level_number")
            .filter(pro_level__level_number=4)
            .count()
        )
        data["nur_no"] = (
            dep.appuser_set.select_related("pro_level__level_number")
            .filter(pro_level__level_number=5)
            .count()
        )
        data["oth_no"] = dep.appuser_set.count() - data["nur_no"] - data["doc_no"]
        data["complaints_against_month"] = dep.complaintsfeedback_set.filter(
            time_filed__month=datetime.today().month
        ).count()
        data["complaints_against_year"] = dep.complaintsfeedback_set.filter(
            time_filed__year=datetime.today().year
        ).count()
        data["complaints_against_last_year"] = dep.complaintsfeedback_set.filter(
            time_filed__year=(datetime.today().year - 1)
        ).count()
        data["pat_no_month"] = dep.patienthealthreccord_set.filter(
            created_date__month=datetime.today().month
        ).count()
        data["pat_no_year"] = dep.patienthealthreccord_set.filter(
            created_date__year=datetime.today().year
        ).count()
        data["pat_no_last_year"] = dep.patienthealthreccord_set.filter(
            created_date__year=(datetime.today().year - 1)
        ).count()
        if not dep.is_medical:
            dick = {"OP" : "", "Transport" : "M_TransportStatistics", "Lab" : "M_LabStatistics", "Rooms" : "M_RoomsStatistics", "Pharmacy" : "M_PharmacyStatistics", "Morgue" : "M_MorgueStatistics"}
            data['stat_url'] = dick[dep.department_name]
        return data


class M_DetailStaffReport(UpdateView):
    model = StaffReport
    fields = ["stop_editing", "dismissed"]
    template_name = "Hospital/StaffReport.html"

    def get_success_url(self):
        return self.request.path_info

    def dispatch(self, request, *args, **kwargs):
        srs = StaffReport.objects.filter(pk=self.kwargs.get("pk"))
        if srs and (
            srs[0].remark_by == request.user.appuser
            or only_managers_of_department(request.user, srs[0].Staff.department)
            or only_above_prof(request.user, 3)
        ):
            return super(M_DetailStaffReport, self).dispatch(request, *args, **kwargs)
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["links"] = get_links(self.request.user.appuser)
        staff = data["object"].Staff
        data["staff"] = staff
        data["base_temp"] = "Hospital/EBase.html" if self.request.user.appuser.pro_level.level_number < 4 else "Hospital/SBase.html"
        data["executive"] = self.request.user.appuser.pro_level.level_number < 4
        data.update(get_staff_statisticts(staff))
        return data


class M_DetailStaffStatistics(TemplateView):
    template_name = "Hospital/StaffReport.html"

    def dispatch(self, request, *args, **kwargs):
        if only_above_prof(request.user, 3):
            return super(M_DetailStaffStatistics, self).dispatch(
                request, *args, **kwargs
            )
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = {"links": get_links(self.request.user.appuser)}
        staff = AppUser.objects.get(pk=self.kwargs.get("pk"))
        data["staff"] = staff
        data["base_temp"] = "Hospital/EBase.html" if self.request.user.appuser.pro_level.level_number < 4 else "Hospital/SBase.html"
        data["executive"] = self.request.user.appuser.pro_level.level_number < 4
        data.update(get_staff_statisticts(staff))
        return data


def get_staff_statisticts(staff):
    data = {}
    atts = staff.attendance_set
    data["absent_monthly"] = atts.filter(
        present=False, time_of_attendance__month=datetime.today().month,
        time_of_attendance__day__lt=datetime.today().day
    ).count()
    data["leaves_month"] = staff.leaveapplications_set.filter(
        canceled=False, approved=True, date__month=datetime.today().month,
        date__day__lt=datetime.today().day
    ).count()
    data["absent_monthly"] -= data["leaves_month"] if data["absent_monthly"] > 0 else 0

    data["absent_yearly"] = atts.filter(
        present=False, time_of_attendance__year=datetime.today().year,
        time_of_attendance__day__lt=datetime.today().day
    ).count()
    data["leaves_year"] = staff.leaveapplications_set.filter(
        date__year=datetime.today().year, canceled=False, approved=True,
        date__day__lt=datetime.today().day
    ).count()
    data["absent_yearly"] -= data["leaves_year"] if data["absent_yearly"] > 0 else 0

    data["absent_last_year"] = atts.filter(
        present=False, time_of_attendance__year=(datetime.today().year - 1)
    ).count()
    data["leaves_last_year"] = staff.leaveapplications_set.filter(
        date__year=(datetime.today().year - 1), canceled=False, approved=True
    ).count()
    data["absent_last_year"] -= data["leaves_last_year"]

    data["complaints_against_month"] = staff.complaints_concerned.filter(
        time_filed__month=datetime.today().month
    ).count()
    data["complaints_against_year"] = staff.complaints_concerned.filter(
        time_filed__year=datetime.today().year
    ).count()
    data["complaints_against_last_year"] = staff.complaints_concerned.filter(
        time_filed__year=(datetime.today().year - 1)
    ).count()
    return data


class M_InventoryReport(TemplateView):
    template_name = "Hospital/InventoryReport.html"

    def dispatch(self, request, *args, **kwargs):
        if only_above_prof(request.user, 3):
            return super(M_InventoryReport, self).dispatch(
                request, *args, **kwargs
            )
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        dep = Department.objects.get(pk=self.kwargs.get("pk"))
        data = {
            "object_list": [
                (obj.item, obj.count) for obj in dep.owned_inventories.all()
            ],
            "department": dep,
        }
        purchases = dep.list_to_buy.filter(aquired_date__year=datetime.today().year)
        data["purchase_year"] = purchases.aggregate(Sum("total_price")).get(
            "total_price__sum"
        )
        data["disc_year"] = purchases.aggregate(Sum("discount")).get("discount__sum")

        purchases = dep.list_to_buy.filter(
            aquired_date__year=(datetime.today().year - 1)
        )
        data["purchase_last_year"] = purchases.aggregate(Sum("total_price")).get(
            "total_price__sum"
        )
        data["disc_last_year"] = purchases.aggregate(Sum("discount")).get(
            "discount__sum"
        )
        return data


class M_DepartmentStatistics(TemplateView):
    template_name = "Hospital/StatMedDep.html"

    def dispatch(self, request, *args, **kwargs):
        if only_above_prof(request.user, 3):
            return super(M_DepartmentStatistics, self).dispatch(
                request, *args, **kwargs
            )
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        department = Department.objects.get(pk=self.kwargs.get("pk"))
        key = self.request.GET.get("years")
        cur_year = datetime.today().year

        monthly = False

        if key == "0" or not key:
            years = [i for i in range(cur_year, cur_year - 51, -1)]
            cases = department.all_cases(years)
            complaints = department.all_complaints(years)
            key = (0, "all")

        elif key == "9":
            year = datetime.today().year
            complaints = department.year_complaints(year)
            cases = department.year_cases(year)
            key = (9, "1( year {0})".format(year))
            monthly = year

        elif key == "99":
            year = datetime.today().year - 1
            complaints = department.year_complaints(year)
            cases = department.year_cases(year)
            key = (99, "1(year {0})".format(year))
            monthly = year

        elif key:
            years = [i for i in range(cur_year, cur_year - (int(key) * 5 + 1)+1, -1)]
            cases = department.all_cases(years)
            complaints = department.all_complaints(years)
            key = (key, int(key) * 5)

        return {
            "cases": cases[0],
            "total_cases": cases[1],
            "department": department,
            "complaints": complaints[0],
            "total_complaints": complaints[1],
            "key": key,
            "monthly": monthly,
        }


class M_LabStatistics(TemplateView):
    template_name = "Hospital/StatLabDep.html"

    def dispatch(self, request, *args, **kwargs):
        if only_above_prof(request.user, 3):
            return super(M_LabStatistics, self).dispatch(
                request, *args, **kwargs
            )
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        department = Department.objects.get(department_name="Lab")
        key = self.request.GET.get("years")
        t_id = self.request.GET.get("test")
        test = None
        if t_id:
            test = Test.objects.get(pk=t_id)

        cur_year = datetime.today().year

        monthly = False

        if key == "0" or not key:
            years = [i for i in range(cur_year, cur_year - 51, -1)]
            tests = all_tests(years, test)
            complaints = department.all_complaints(years)
            key = (0, "all")

        elif key == "9":
            complaints = department.year_complaints(datetime.today().year)
            tests = all_tests_current_year(test)
            key = (9, 1)
            monthly = True

        elif key:
            years = [i for i in range(cur_year, cur_year - (int(key) * 5 + 1), -1)]
            tests = all_tests(years, test)
            complaints = department.all_complaints(years)
            key = (key, int(key) * 5)

        data = {
            "cur_test": test,
            "select_tests": Test.objects.all(),
            "tests": tests[0],
            "total_tests": tests[1],
            "department": department,
            "complaints": complaints[0],
            "total_complaints": complaints[1],
            "key": key,
            "monthly": monthly,
        }

        return data


class M_RoomsStatistics(TemplateView):
    template_name = "Hospital/StatRoomsDep.html"

    def dispatch(self, request, *args, **kwargs):
        if only_above_prof(request.user, 3):
            return super(M_RoomsStatistics, self).dispatch(
                request, *args, **kwargs
            )
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        department = Department.objects.get(department_name="Lab")
        key = self.request.GET.get("years")
        t_id = self.request.GET.get("type")
        rtype = None
        if t_id:
            rtype = RoomType.objects.get(pk=t_id)

        cur_year = datetime.today().year

        monthly = False
        if key == "0" or not key:
            years = [i for i in range(cur_year, cur_year - 51, -1)]
            admissions = all_admissions(years, rtype)
            complaints = department.all_complaints(years)
            key = (0, "all")

        elif key == "9":
            complaints = department.year_complaints(datetime.today().year)
            admissions = all_admissions_current_year(rtype)
            key = (9, 1)
            monthly = True

        elif key:
            years = [i for i in range(cur_year, cur_year - (int(key) * 5 + 1), -1)]
            complaints = department.all_complaints(years)
            admissions = all_admissions(years, rtype)
            key = (key, int(key) * 5)

        data = {
            "cur_type": rtype,
            "select_types": RoomType.objects.all(),
            "admissions": admissions[0],
            "total_admissions": admissions[1],
            "department": department,
            "complaints": complaints[0],
            "total_complaints": complaints[1],
            "key": key,
            "monthly": monthly,
        }

        return data


class M_MorgueStatistics(TemplateView):
    template_name = "Hospital/StatMorgueDep.html"

    def dispatch(self, request, *args, **kwargs):
        if only_above_prof(request.user, 3):
            return super(M_MorgueStatistics, self).dispatch(
                request, *args, **kwargs
            )
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        department = Department.objects.get(department_name = "Morgue")
        key = self.request.GET.get("years")

        cur_year = datetime.today().year

        monthly = False
        if key == "0" or not key:
            years = [i for i in range(cur_year, cur_year - 51, -1)]
            admissions = all_morgues(years)
            complaints = department.all_complaints(years)
            key = (0, "all")

        elif key == "9":
            complaints = department.year_complaints(datetime.today().year)
            admissions = morgues_year(cur_year)
            key = (9, 1)
            monthly = True

        elif key:
            years = [i for i in range(cur_year, cur_year - (int(key) * 5 + 1), -1)]
            complaints = department.all_complaints(years)
            admissions = all_morgues(years)
            key = (key, int(key) * 5)

        data = {
            "select_types": RoomType.objects.all(),
            "admissions": admissions[0],
            "total_admissions": admissions[1],
            "department": department,
            "complaints": complaints[0],
            "total_complaints": complaints[1],
            "key": key,
            "monthly": monthly,
        }

        return data


class M_PharmacyStatistics(TemplateView):
    template_name = "Hospital/StatPharDep.html"

    def dispatch(self, request, *args, **kwargs):
        if only_above_prof(request.user, 3):
            return super(M_PharmacyStatistics, self).dispatch(
                request, *args, **kwargs
            )
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        department = Department.objects.get(department_name="Lab")
        key = self.request.GET.get("years")
        med_id = self.request.GET.get("med")
        medicine = None
        if med_id:
            medicine = Medicine.objects.get(pk=med_id)

        cur_year = datetime.today().year

        monthly = False
        if key == "0" or not key:
            years = [i for i in range(cur_year, cur_year - 51, -1)]
            medications = all_medications(years, medicine)
            complaints = department.all_complaints(years)
            key = (0, "all")

        elif key == "9":
            complaints = department.year_complaints(datetime.today().year)
            medications = all_medications_current_year(medicine)
            key = (9, 1)
            monthly = True

        elif key:
            years = [i for i in range(cur_year, cur_year - (int(key) * 5 + 1), -1)]
            complaints = department.all_complaints(years)
            medications = all_medications(years, medicine)
            key = (key, int(key) * 5)

        data = {
            "cur_med": medicine,
            "select_meds": Medicine.objects.all(),
            "medications": medications[0],
            "total_medications": medications[1],
            "department": department,
            "complaints": complaints[0],
            "total_complaints": complaints[1],
            "key": key,
            "monthly": monthly,
        }

        return data


class M_TransportStatistics(TemplateView):
    template_name = "Hospital/StatTranspep.html"

    def dispatch(self, request, *args, **kwargs):
        if only_above_prof(request.user, 3):
            return super(M_TransportStatistics, self).dispatch(
                request, *args, **kwargs
            )
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        department = Department.objects.get(department_name="Transport")
        key = self.request.GET.get("years")
        d_id = self.request.GET.get("dep")
        inv_id = self.request.GET.get("inv")
        dep = None
        inv = None
        if d_id:
            dep = Department.objects.get(pk=d_id)

        if inv_id:
            inv = Inventory.objects.get(pk=inv_id)

        cur_year = datetime.today().year

        monthly = False
        if key == "0" or not key:
            years = [i for i in range(cur_year, cur_year - 51, -1)]
            purchases = all_purchases(years, dep, inv)
            complaints = department.all_complaints(years)
            key = (0, "all")

        elif key == "9":
            complaints = department.year_complaints(datetime.today().year)
            purchases = all_purchases_current_year(dep, inv)
            key = (9, 1)
            monthly = True

        elif key:
            years = [i for i in range(cur_year, cur_year - (int(key) * 5 + 1), -1)]
            complaints = department.all_complaints(years)
            purchases = all_purchases(years, dep, inv)
            key = (key, int(key) * 5)

        data = {
            "cur_dep": dep,
            "cur_inv": inv,
            "select_deps": Department.objects.all(),
            "select_invs": Inventory.objects.all(),
            "purchases": purchases[0],
            "total_purchases": purchases[1],
            "department": department,
            "complaints": complaints[0],
            "total_complaints": complaints[1],
            "key": key,
            "monthly": monthly,
        }

        return data


class M_DiseaseStatistics(TemplateView):
    template_name = "Hospital/StatDisease.html"

    def dispatch(self, request, *args, **kwargs):
        if only_above_prof(request.user, 3):
            return super(M_DiseaseStatistics, self).dispatch(
                request, *args, **kwargs
            )
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        disease_ids = []
        cur_dis = []
        for i in range(4):
            if self.request.GET.get('dis{0}'.format(i)):
                disease_ids.append(self.request.GET.get('dis{0}'.format(i)))
        if disease_ids:
            diseases = Disease.objects.filter(id__in = disease_ids)
            cur_dis = diseases
        else:
            diseases = Disease.objects.all()

        key = self.request.GET.get("years")
        cur_year = datetime.today().year
        if key == "0" or not key:
            years = [i for i in range(cur_year, cur_year - 51, -1)]
            dis_report = all_diceases(years, diseases)
            key = (0, "all")

        elif key == "9":
            years = [mon for mon in calendar.month_name[1:]]
            dis_report = all_diceases_year(cur_year, diseases)
            key = (9, "1(year {0})".format(cur_year))

        elif key == "99":
            years = [mon for mon in calendar.month_name[1:]]
            dis_report = all_diceases_year(cur_year - 1, diseases)
            key = (99, "1(year {0})".format(cur_year-1))

        elif key:
            years = [i for i in range(cur_year, cur_year - (int(key) * 5 + 1), -1)]            
            dis_report = all_diceases(years, diseases)
            key = (key, int(key) * 5)

        heads = [[d.disease_name, str(d.fatality_rate)] for d in diseases]
        data = {
            "cur_dis": cur_dis,
            "select_diseases": Disease.objects.all(),
            "select_causes" : CauseOfDisease.objects.all(),
            "dis_reports": simplejson.dumps(dis_report[0]),
            "key": key,
            "heads" : simplejson.dumps(heads),
            'years' : simplejson.dumps(years),
            'count_list' : simplejson.dumps(dis_report[1])
            }
        return data


class M_DepartmentManagers(View):
    def dispatch(self, request, *args, **kwargs):
        if only_above_prof(request.user, 3):
            return super(M_DepartmentManagers, self).dispatch(
                request, *args, **kwargs
            )
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get(self, request, *args, **kwargs):
        department = Department.objects.get(pk = self.kwargs.get('pk'))
        mans = department.departmentmanager_set.all()
        return render(request, "Hospital/DepartmentManagers.html", {'department' : department, 'extisting_managers' : mans})
    

class M_NewDepartmentManager(CreateView):
    model = DepartmentManager
    fields = ['manager']
    template_name = "Hospital/create.html"

    def dispatch(self, request, *args, **kwargs):
        if only_above_prof(request.user, 3):
            return super(M_NewDepartmentManager, self).dispatch(
                request, *args, **kwargs
            )
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        dep = Department.objects.get(pk = self.kwargs.get('pk'))
        data['base_temp'] = "Hospital/EBase.html"
        data['head'] = "appoint manager for the department of {0}".format(dep)
        data['form'].fields['manager'].queryset = dep.appuser_set.all()
        return data

    def form_valid(self, form):
        dep_man = form.save(commit = False)
        dep = Department.objects.get(pk = self.kwargs.get('pk'))
        dep_man.department = dep
        dep_man.save()
        return redirect("M_DepartmentManagers", pk = dep.id)


class M_AppointDepartmentManager(UpdateView):
    model = DepartmentManager
    fields = ['manager']
    template_name = "Hospital/Update.html"

    def dispatch(self, request, *args, **kwargs):
        if only_above_prof(request.user, 3):
            return super(M_AppointDepartmentManager, self).dispatch(
                request, *args, **kwargs
            )
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_success_url(self):
        return reverse_lazy("M_Departments")

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['base_temp'] = "Hospital/EBase.html"
        data['head'] = "change manager for the department of {0}".format(data['object'].department)
        data['form'].fields['manager'].queryset = data['object'].department.appuser_set.all()
        return data

    def form_valid(self, form):
        dep_man = DepartmentManager.objects.get(pk = self.kwargs.get('pk'))
        dep = dep_man.department
        if self.request.POST.get('deletable') == 'delete':
            dep_man.delete()
        else:
            super().form_valid(form)
        return redirect("M_DepartmentManagers", pk = dep.id)


class M_PromoOrDepromo(UpdateView):
    model = AppUser
    fields = ['pro_level']
    template_name = "Hospital/UpdateWithoutDelete.html"

    def get_success_url(self):
        return reverse_lazy("M_StaffReports", kwargs = {"pk" : self.kwargs.get('pk')})

    def dispatch(self, request, *args, **kwargs):
        if only_above_prof(request.user, 3):
            return super(M_PromoOrDepromo, self).dispatch(
                request, *args, **kwargs
            )
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['base_temp'] = "Hospital/EBase.html"
        data["form"].fields["pro_level"].queryset = Level.objects.filter(level_number__gt = 3)
        data['head'] = "promote/Depromote {0}".format(data['object'].app_user)
        return data

class M_StaffWithoutShift(TemplateView):
    template_name = "Hospital/object_list.html"

    def dispatch(self, request, *args, **kwargs):
        if only_above(request.user, 3):
            return super(M_StaffWithoutShift, self).dispatch(
                request, *args, **kwargs
            )
        else:
            return render(
                request, "Hospital/Unauthorized.html", {"link": ("DHome", "Go Home")}
            )

    def get_context_data(self, **kwargs):
        staff_levels = Level.objects.filter(level_number__gt = 3)
        data = {"object_list" : AppUser.objects.filter(department = None, pro_level__in = staff_levels, occupabili = True)}
        data["head"] = "unassigned staffs"
        data["edit_url"] = "ChangeShiftDep"
        data["base_temp"] = "Hospital/EBase.html"
        data["info"] = "staffs under disciplinary action are not shown here unless the disciplinary action is complete."
        data["links"] = get_links(self.request.user.appuser)
        return data


class Manual(TemplateView):
    template_name = "Hospital/manuals/manual.html"