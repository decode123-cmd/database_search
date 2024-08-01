# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class BrowseByPatientStudies(models.Model):
    id = models.TextField(db_column='ID', blank=True, null=True)  # Field name made lowercase.
    drug = models.TextField(db_column='DRUG', blank=True, null=True)  # Field name made lowercase.
    drug_category = models.TextField(db_column='Drug category', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    drugbank_id = models.TextField(db_column='Drugbank_ID', blank=True, null=True)  # Field name made lowercase.
    target_s_or_mechanism_of_action = models.TextField(db_column='TARGET/s OR MECHANISM OF ACTION', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    kegg_drug_id = models.TextField(db_column='KEGG DRUG ID', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    drug_pubchem = models.TextField(db_column='DRUG_PUBCHEM', blank=True, null=True)  # Field name made lowercase.
    str_link_smiles_field = models.TextField(db_column='STR_LINK (SMILES)', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters. Field renamed because it ended with '_'.
    single_combination = models.TextField(db_column='Single/Combination', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    pmid = models.TextField(db_column='PMID', blank=True, null=True)  # Field name made lowercase.
    cancer_type = models.TextField(db_column='Cancer_Type', blank=True, null=True)  # Field name made lowercase.
    cancer_type_description = models.TextField(db_column='Cancer_Type Description', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    patient_sample = models.TextField(db_column='PATIENT_SAMPLE', blank=True, null=True)  # Field name made lowercase.
    male_female = models.TextField(db_column='MALE/FEMALE', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    median_age_range = models.TextField(db_column='MEDIAN AGE/RANGE', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    dose = models.TextField(db_column='DOSE', blank=True, null=True)  # Field name made lowercase.
    technique = models.TextField(db_column='TECHNIQUE', blank=True, null=True)  # Field name made lowercase.
    immune_system_function_enhanced_numbers_increased = models.TextField(db_column='IMMUNE SYSTEM-Function enhanced/numbers increased', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    immune_system_function_inhibited_numbers_decreased = models.TextField(db_column='IMMUNE SYSTEM-Function inhibited/numbers decreased', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    immune_sytem_function_unaffected = models.TextField(db_column='IMMUNE SYTEM FUNCTION UNAFFECTED', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    negative_immune_sytem_regulation_function_enhanced_numbers_incr = models.TextField(db_column='NEGATIVE IMMUNE SYTEM REGULATION-Function enhanced/numbers incr', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    tertiary_remark = models.TextField(db_column='TERTIARY_REMARK', blank=True, null=True)  # Field name made lowercase.
    comment = models.TextField(db_column='COMMENT', blank=True, null=True)  # Field name made lowercase.
    unnamed_23 = models.TextField(db_column='Unnamed: 23', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.

    class Meta:
        managed = False
        db_table = 'Browse_by_Patient_Studies'


class BrowseByAnimalStudies(models.Model):
    id = models.TextField(db_column='ID', blank=True, null=True)  # Field name made lowercase.
    drug = models.TextField(db_column='DRUG', blank=True, null=True)  # Field name made lowercase.
    drug_category = models.TextField(db_column='Drug category', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    drugbank_id = models.TextField(db_column='Drugbank_ID', blank=True, null=True)  # Field name made lowercase.
    target_s_or_mechanism_of_action = models.TextField(db_column='TARGET/s OR MECHANISM OF ACTION', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    kegg_drug_id = models.TextField(db_column='KEGG DRUG ID', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    drug_pubchem = models.TextField(db_column='DRUG_PUBCHEM', blank=True, null=True)  # Field name made lowercase.
    str_link_smiles_field = models.TextField(db_column='STR_LINK (SMILES)', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters. Field renamed because it ended with '_'.
    single_combination = models.TextField(db_column='Single/Combination', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    pmid = models.TextField(db_column='PMID', blank=True, null=True)  # Field name made lowercase.
    cancer_type = models.TextField(db_column='Cancer_Type', blank=True, null=True)  # Field name made lowercase.
    cancer_type_description = models.TextField(db_column='Cancer_Type Description', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    animal_strain_used = models.TextField(db_column='ANIMAL STRAIN USED', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    cell_line_used_to_induce_tumor_in_mice = models.TextField(db_column='CELL LINE USED TO INDUCE TUMOR IN MICE', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    dose = models.TextField(db_column='DOSE', blank=True, null=True)  # Field name made lowercase.
    technique = models.TextField(db_column='Technique', blank=True, null=True)  # Field name made lowercase.
    immune_system_function_enhanced_numbers_increased = models.TextField(db_column='IMMUNE SYSTEM-Function enhanced/numbers increased', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    immune_system_function_inhibited_numbers_decreased = models.TextField(db_column='IMMUNE SYSTEM-Function inhibited/numbers decreased', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    immune_sytem_function_unaffected = models.TextField(db_column='IMMUNE SYTEM FUNCTION UNAFFECTED', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    negative_immune_sytem_regulation_function_enhanced_numbers_incr = models.TextField(db_column='NEGATIVE IMMUNE SYTEM REGULATION-Function enhanced/numbers incr', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    tertiary_remark = models.TextField(db_column='TERTIARY_REMARK', blank=True, null=True)  # Field name made lowercase.
    comment = models.TextField(db_column='COMMENT', blank=True, null=True)  # Field name made lowercase.
    unnamed_22 = models.TextField(db_column='Unnamed: 22', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.

    class Meta:
        managed = False
        db_table = 'Browse_by_animal_studies'


class BrowseByCellLine(models.Model):
    id = models.TextField(db_column='ID', blank=True, null=True)  # Field name made lowercase.
    drug = models.TextField(db_column='DRUG', blank=True, null=True)  # Field name made lowercase.
    drug_category = models.TextField(db_column='Drug category', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    drugbank_id = models.TextField(db_column='Drugbank_ID', blank=True, null=True)  # Field name made lowercase.
    target_s_or_mechanism_of_action = models.TextField(db_column='TARGET/s OR MECHANISM OF ACTION', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    kegg_drug_id = models.TextField(db_column='KEGG DRUG ID', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    drug_pubchem = models.TextField(db_column='DRUG_PUBCHEM', blank=True, null=True)  # Field name made lowercase.
    str_link_smiles_field = models.TextField(db_column='STR_LINK (SMILES)', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters. Field renamed because it ended with '_'.
    single_combination = models.TextField(db_column='Single/Combination', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    pmid = models.TextField(db_column='PMID', blank=True, null=True)  # Field name made lowercase.
    cancer_type = models.TextField(db_column='Cancer_Type', blank=True, null=True)  # Field name made lowercase.
    cancer_type_description = models.TextField(db_column='Cancer_Type Description', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    system = models.TextField(db_column='SYSTEM', blank=True, null=True)  # Field name made lowercase.
    dose = models.TextField(db_column='DOSE', blank=True, null=True)  # Field name made lowercase.
    technique = models.TextField(db_column='TECHNIQUE', blank=True, null=True)  # Field name made lowercase.
    immune_system_function_enhanced_numbers_increased = models.TextField(db_column='IMMUNE SYSTEM-Function enhanced/numbers increased', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    immune_system_function_inhibited_numbers_decreased = models.TextField(db_column='IMMUNE SYSTEM-Function inhibited/numbers decreased', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    immune_sytem_function_unaffected = models.TextField(db_column='IMMUNE SYTEM FUNCTION UNAFFECTED', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    negative_immune_sytem_regulation_function_enhanced_numbers_incr = models.TextField(db_column='NEGATIVE IMMUNE SYTEM REGULATION-Function enhanced/numbers incr', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    tertiary_remark = models.TextField(db_column='TERTIARY_REMARK', blank=True, null=True)  # Field name made lowercase.
    comment = models.TextField(db_column='COMMENT', blank=True, null=True)  # Field name made lowercase.
    unnamed_21 = models.TextField(db_column='Unnamed: 21', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.

    class Meta:
        managed = False
        db_table = 'Browse_by_cell_line'


class BrowseByIndex(models.Model):
    drug_category = models.TextField(db_column='Drug category', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    cell_line = models.TextField(db_column='Cell Line', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    animal_studies = models.TextField(db_column='Animal Studies', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    cancer_patients = models.TextField(db_column='Cancer Patients', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    unnamed_4 = models.TextField(db_column='Unnamed: 4', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    cancer_type = models.TextField(db_column='Cancer_Type', blank=True, null=True)  # Field name made lowercase.
    cell_line_1 = models.TextField(db_column='Cell Line.1', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    animal_studies_1 = models.TextField(db_column='Animal Studies.1', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    cancer_patients_1 = models.TextField(db_column='Cancer Patients.1', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    unnamed_9 = models.TextField(db_column='Unnamed: 9', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    assay_technique = models.TextField(db_column='Assay /Technique', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    cell_line_2 = models.TextField(db_column='Cell Line.2', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    animal_studies_2 = models.TextField(db_column='Animal Studies.2', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    cancer_patients_2 = models.TextField(db_column='Cancer Patients.2', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.

    class Meta:
        managed = False
        db_table = 'Browse_by_index'


class Master(models.Model):
    id = models.TextField(db_column='ID', blank=True, null=True)  # Field name made lowercase.
    drug = models.TextField(db_column='DRUG', blank=True, null=True)  # Field name made lowercase.
    drug_category = models.TextField(db_column='Drug category', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    drugbank_id = models.TextField(db_column='Drugbank_ID', blank=True, null=True)  # Field name made lowercase.
    target_s_or_mechanism_of_action = models.TextField(db_column='TARGET/s OR MECHANISM OF ACTION', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    kegg_drug_id = models.TextField(db_column='KEGG DRUG ID', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    drug_pubchem = models.TextField(db_column='DRUG_PUBCHEM', blank=True, null=True)  # Field name made lowercase.
    str_link_smiles_field = models.TextField(db_column='STR_LINK (SMILES)', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters. Field renamed because it ended with '_'.
    single_combination = models.TextField(db_column='Single/Combination', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    pmid = models.TextField(db_column='PMID', blank=True, null=True)  # Field name made lowercase.
    cancer_type = models.TextField(db_column='Cancer_Type', blank=True, null=True)  # Field name made lowercase.
    cancer_type_description = models.TextField(db_column='Cancer_Type Description', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    animal_strain_used = models.TextField(db_column='ANIMAL STRAIN USED', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    cell_line_used_to_induce_tumor_in_mice = models.TextField(db_column='CELL LINE USED TO INDUCE TUMOR IN MICE', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    dose = models.TextField(db_column='DOSE', blank=True, null=True)  # Field name made lowercase.
    technique_1 = models.TextField(db_column='Technique_1', blank=True, null=True)  # Field name made lowercase.
    patient_sample = models.TextField(db_column='PATIENT_SAMPLE', blank=True, null=True)  # Field name made lowercase.
    male_female = models.TextField(db_column='MALE/FEMALE', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    median_age_range = models.TextField(db_column='MEDIAN AGE/RANGE', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    dose_1 = models.TextField(db_column='DOSE.1', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    technique_4 = models.TextField(db_column='TECHNIQUE_4', blank=True, null=True)  # Field name made lowercase.
    technique_3 = models.TextField(db_column='TECHNIQUE_3', blank=True, null=True)  # Field name made lowercase.
    system = models.TextField(db_column='SYSTEM', blank=True, null=True)  # Field name made lowercase.
    dose_2 = models.TextField(db_column='DOSE.2', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    technique_2 = models.TextField(db_column='TECHNIQUE_2', blank=True, null=True)  # Field name made lowercase.
    immune_system_function_enhanced_numbers_increased = models.TextField(db_column='IMMUNE SYSTEM-Function enhanced/numbers increased', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    immune_system_function_inhibited_numbers_decreased = models.TextField(db_column='IMMUNE SYSTEM-Function inhibited/numbers decreased', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    immune_sytem_function_unaffected = models.TextField(db_column='IMMUNE SYTEM FUNCTION UNAFFECTED', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    negative_immune_sytem_regulation = models.TextField(db_column='NEGATIVE IMMUNE SYTEM REGULATION', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    tertiary_remark = models.TextField(db_column='TERTIARY_REMARK', blank=True, null=True)  # Field name made lowercase.
    comment = models.TextField(db_column='COMMENT', blank=True, null=True)  # Field name made lowercase.
    unnamed_31 = models.TextField(db_column='Unnamed: 31', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.

    class Meta:
        managed = False
        db_table = 'Master'


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.SmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class Users(models.Model):
    id = models.TextField(db_column='ID', blank=True, null=True)  # Field name made lowercase.
    drug = models.TextField(db_column='DRUG', blank=True, null=True)  # Field name made lowercase.
    drug_category = models.TextField(db_column='Drug category', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    drugbank_id = models.TextField(db_column='Drugbank_ID', blank=True, null=True)  # Field name made lowercase.
    target_s_or_mechanism_of_action = models.TextField(db_column='TARGET/s OR MECHANISM OF ACTION', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    kegg_drug_id = models.TextField(db_column='KEGG DRUG ID', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    drug_pubchem = models.TextField(db_column='DRUG_PUBCHEM', blank=True, null=True)  # Field name made lowercase.
    str_link_smiles_field = models.TextField(db_column='STR_LINK (SMILES)', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters. Field renamed because it ended with '_'.
    single_combination = models.TextField(db_column='Single/Combination', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    pmid = models.TextField(db_column='PMID', blank=True, null=True)  # Field name made lowercase.
    cancer_type = models.TextField(db_column='Cancer_Type', blank=True, null=True)  # Field name made lowercase.
    cancer_type_description = models.TextField(db_column='Cancer_Type Description', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    animal_strain_used = models.TextField(db_column='ANIMAL STRAIN USED', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    cell_line_used_to_induce_tumor_in_mice = models.TextField(db_column='CELL LINE USED TO INDUCE TUMOR IN MICE', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    dose = models.TextField(db_column='DOSE', blank=True, null=True)  # Field name made lowercase.
    technique_1 = models.TextField(db_column='Technique_1', blank=True, null=True)  # Field name made lowercase.
    patient_sample = models.TextField(db_column='PATIENT_SAMPLE', blank=True, null=True)  # Field name made lowercase.
    male_female = models.TextField(db_column='MALE/FEMALE', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    median_age_range = models.TextField(db_column='MEDIAN AGE/RANGE', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    dose_1 = models.TextField(db_column='DOSE.1', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    technique_4 = models.TextField(db_column='TECHNIQUE_4', blank=True, null=True)  # Field name made lowercase.
    technique_3 = models.TextField(db_column='TECHNIQUE_3', blank=True, null=True)  # Field name made lowercase.
    system = models.TextField(db_column='SYSTEM', blank=True, null=True)  # Field name made lowercase.
    dose_2 = models.TextField(db_column='DOSE.2', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    technique_2 = models.TextField(db_column='TECHNIQUE_2', blank=True, null=True)  # Field name made lowercase.
    immune_system_function_enhanced_numbers_increased = models.TextField(db_column='IMMUNE SYSTEM-Function enhanced/numbers increased', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    immune_system_function_inhibited_numbers_decreased = models.TextField(db_column='IMMUNE SYSTEM-Function inhibited/numbers decreased', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    immune_sytem_function_unaffected = models.TextField(db_column='IMMUNE SYTEM FUNCTION UNAFFECTED', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    negative_immune_sytem_regulation = models.TextField(db_column='NEGATIVE IMMUNE SYTEM REGULATION', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    tertiary_remark = models.TextField(db_column='TERTIARY_REMARK', blank=True, null=True)  # Field name made lowercase.
    comment = models.TextField(db_column='COMMENT', blank=True, null=True)  # Field name made lowercase.
    unnamed_31 = models.TextField(db_column='Unnamed: 31', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.

    class Meta:
        managed = False
        db_table = 'users'
