from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
from .models import Profile, Report, Image, OperationLine, Profession, Solution, SubCategory, SubCategoryForUser
from django import forms
from django.contrib.auth.models import Group
# Register your models here.

# custom filters 

class ProfessionFilter(admin.SimpleListFilter):
    title = 'Profession'
    parameter_name = 'profession'

    def lookups(self, request, model_admin):
        professions = Profession.objects.all()
        return [(profession.id, profession.profession_name) for profession in professions]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(profile__profession__id=self.value())
        return queryset

class OperationLineFilter(admin.SimpleListFilter):
    title = 'Operation Line'
    parameter_name = 'operationLineNo'

    def lookups(self, request, model_admin):
        operation_lines = OperationLine.objects.all()
        return [(operation_line_no.id, operation_line_no) for operation_line_no in operation_lines]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(profile__operation_line_no__id=self.value())
        return queryset
    
# End of custom filters
from django.contrib import admin
from .models import Report, Image, Solution, ImageSolution
from django.utils.html import format_html

class ImageInline(admin.TabularInline):
    model = Image
    extra = 0
    readonly_fields = ('image_thumbnail',)

    def image_thumbnail(self, obj):
        return format_html('<img src="{}" width="100" height="100" />'.format(obj.imageData.url))
    image_thumbnail.short_description = 'Thumbnail'

class ImageForSolutionInline(admin.TabularInline):
    model = ImageSolution
    extra = 0
    readonly_fields = ('image_thumbnail',)

    def image_thumbnail(self, obj):
        return format_html('<img src="{}" width="100" height="100" />'.format(obj.imageData.url))
    image_thumbnail.short_description = 'Thumbnail'
    
# # Inline for images associated with a solution
# class ImageForSolutionInline(admin.TabularInline):
#     model = ImageSolution
#     extra = 0

# Inline for Solution, including the ImageForSolutionInline
class SolutionInline(admin.StackedInline):
    model = Solution
    extra = 0
    readonly_fields = ('solverName',  'description', 'datetime')
    can_delete = False
    show_change_link = True  # Allows navigating to the solution's change form
    inlines = [ImageForSolutionInline]

# Inline for images associated with a report
# class ImageInline(admin.TabularInline):
#     model = Image
#     extra = 0

# Admin for Report, including the SolutionInline and ImageInline
class ReportAdmin(admin.ModelAdmin):
    inlines = [ImageInline,SolutionInline]
    list_filter = ('status',)
    list_display = ('reportID', 'reporterName', 'operationLineNumber', 'problemCategory', 'status', 'datetime')

admin.site.register(Report, ReportAdmin)

# Separate admin for Solution to display on its own
class SolutionAdmin(admin.ModelAdmin):
    inlines = [ImageForSolutionInline]
    list_display = ('solutionID', 'report', 'solverName', 'datetime')
    readonly_fields = ('report',)

admin.site.register(Solution, SolutionAdmin)




# Adding more options for Operation Line No and profession
class ProfileAdminForm(forms.ModelForm):
    operation_line_no = forms.ModelMultipleChoiceField(
        queryset=OperationLine.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    
    profession = forms.ModelMultipleChoiceField(
        queryset=Profession.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = Profile
        fields = '__all__'

class OperationLineInline(admin.TabularInline):
    model = Profile.operation_line_no.through
    extra = 1


class ProfessionInline(admin.TabularInline):
    model = Profile.profession.through
    extra = 1

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    form = ProfileAdminForm
    inlines = [OperationLineInline, ProfessionInline]
 

# for user diaplay
class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline,)
    list_display = ('username', 'get_groups', 'get_operation_lines', 'get_profession')
    list_filter = ('groups', OperationLineFilter, ProfessionFilter)
    exclude = ('user_permissions', 'important_dates')  # Excluded fields
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    def get_groups(self, obj):
        return ", ".join([group.name for group in obj.groups.all()])
    get_groups.short_description = 'Groups'
    
    def get_operation_lines(self, obj):
        profile = Profile.objects.get(user=obj)
        return ", ".join([operation_line_no.line_no for operation_line_no in profile.operation_line_no.all()])
    get_operation_lines.short_description = 'Operation Lines'
    
    def get_profession(self, obj):
        profile = Profile.objects.get(user=obj)
        return ", ".join([profession.profession_name for profession in profile.profession.all()])
    get_profession.short_description = 'Profession'


from django.contrib import admin
from .models import Profession, SubCategory, SubCategoryForUser

# Inline admin for SubCategory
class SubCategoryInline(admin.TabularInline):
    model = Profession.subCategory.through
    extra = 1

# Inline admin for SubCategoryForUser
class SubCategoryForUserInline(admin.TabularInline):
    model = Profession.subCategoryForUser.through
    extra = 1

# Custom admin for Profession
class ProfessionAdmin(admin.ModelAdmin):
    list_display = ('profession_name',)
    inlines = [SubCategoryInline, SubCategoryForUserInline]
    exclude = ('subCategory', 'subCategoryForUser')

# Register the Profession model with the custom admin class
admin.site.register(Profession, ProfessionAdmin)

# Register the SubCategory model
admin.site.register(SubCategory)

# Register the SubCategoryForUser model
admin.site.register(SubCategoryForUser)

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(OperationLine)

