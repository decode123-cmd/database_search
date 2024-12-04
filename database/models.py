from django.db import models

from django.db import models

class CellStudy(models.Model):
    # Fields for the Anti-Cancer Drug information
    id = models.AutoField(primary_key=True)
    drug = models.CharField(max_length=255)
    drug_category = models.CharField(max_length=255)
    drugbank_id = models.CharField(max_length=255)
    target_or_mechanism_of_action = models.TextField()
    kegg_drug_id = models.CharField(max_length=255)
    pubchem_id = models.CharField(max_length=255)
    str_link_smiles = models.CharField(max_length=255)
    single_or_combination = models.CharField(max_length=50)
    pmid = models.CharField(max_length=255)
    cancer_type = models.CharField(max_length=255)
    cancer_type_description = models.TextField()
    system = models.CharField(max_length=255)
    dose = models.CharField(max_length=255)
    technique = models.CharField(max_length=255)
    immune_system_function_enhanced = models.CharField(max_length=255)
    immune_system_function_inhibited = models.CharField(max_length=255)
    immune_system_function_unaffected = models.CharField(max_length=255)
    negative_immune_system_regulation = models.CharField(max_length=255)
    
    # Fields for additional information
    submitter_name = models.CharField(max_length=255)
    email_address = models.EmailField()
    mailing_address = models.TextField(blank=True, null=True)
    comment_or_suggestion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.drug  # Return the drug name as string representation

class AnimalStudy(models.Model):
    # Drug Information
    id = models.AutoField(primary_key=True)
    drug = models.CharField(max_length=255)
    drug_category = models.CharField(max_length=255)
    drugbank_id = models.CharField(max_length=255)
    target_or_mechanism_of_action = models.TextField()
    kegg_drug_id = models.CharField(max_length=255)
    drug_pubchem = models.CharField(max_length=255)
    str_link_smiles = models.CharField(max_length=255)
    single_or_combination = models.CharField(max_length=50)
    pmid = models.CharField(max_length=255)
    cancer_type = models.CharField(max_length=255)
    cancer_type_description = models.TextField()

    # Animal Study Information
    animal_strain_used = models.CharField(max_length=255)
    cell_line_used_to_induce_tumor_in_mice = models.CharField(max_length=255)

    # Treatment Information
    dose = models.CharField(max_length=255)
    technique = models.CharField(max_length=255)

    # Immune system-related information
    immune_system_function_enhanced = models.CharField(max_length=255)
    immune_system_function_inhibited = models.CharField(max_length=255)
    immune_system_function_unaffected = models.CharField(max_length=255)
    negative_immune_system_regulation = models.CharField(max_length=255)

    # Submitter Information
    submitter_name = models.CharField(max_length=255)
    email_address = models.EmailField()
    mailing_address = models.TextField(blank=True, null=True)
    comment_or_suggestion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.drug  # Display the drug name in admin and other views

class PatientStudy(models.Model):
   # Fields for the Anti-Cancer Drug information
    id = models.AutoField(primary_key=True)
    drug = models.CharField(max_length=255)
    drug_category = models.CharField(max_length=255)
    drugbank_id = models.CharField(max_length=255)
    target_or_mechanism_of_action = models.TextField()
    kegg_drug_id = models.CharField(max_length=255)
    pubchem_id = models.CharField(max_length=255)
    str_link_smiles = models.CharField(max_length=255)
    single_or_combination = models.CharField(max_length=50)
    pmid = models.CharField(max_length=255)
    cancer_type = models.CharField(max_length=255)
    cancer_type_description = models.TextField()
    
    # Patient Information
    patient_sample = models.CharField(max_length=255)
    male_or_female = models.CharField(max_length=6)  # Male/Female
    median_age_or_range = models.CharField(max_length=255)  # Median age or range
    
    # Drug Dose and Technique
    dose = models.CharField(max_length=255)
    technique = models.CharField(max_length=255)

    # Immune system-related information
    immune_system_function_enhanced = models.CharField(max_length=255)
    immune_system_function_inhibited = models.CharField(max_length=255)
    immune_system_function_unaffected = models.CharField(max_length=255)
    negative_immune_system_regulation = models.CharField(max_length=255)
    
    # Fields for additional information
    submitter_name = models.CharField(max_length=255)
    email_address = models.EmailField()
    mailing_address = models.TextField(blank=True, null=True)
    comment_or_suggestion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.drug  # Return the drug name as string representation


