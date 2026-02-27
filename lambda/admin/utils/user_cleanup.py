"""
User Data Cleanup Functions
Comprehensive deletion across all 10 DynamoDB tables
"""

from shared.dynamodb import Quota, UserInfo, UserRole
from .models import (
    ProjectUsers,
    ClinicJobs,
    ClinicalAnnotations,
    ClinicalVariants,
    JupyterInstances,
    SavedQueries,
    CliUpload,
)


def delete_user_data_from_all_tables(uid: str) -> dict:
    """
    Delete user data from all 10 DynamoDB tables.
    
    Args:
        uid: User ID (Cognito sub)
        
    Returns:
        Dictionary with cleanup results:
        {
            "deleted": [...],      # List of deleted items
            "not_found": [...],    # Tables with no data
            "errors": [...]        # Any errors encountered
        }
        
    Safe to run - skips if data already clean, no errors thrown.
    """
    results = {
        "deleted": [],
        "not_found": [],
        "errors": []
    }
    
    print(f"[USER CLEANUP] Starting data deletion for user: {uid}")
    
    # 1. Delete from ProjectUsers (query by uid, then delete each project)
    try:
        print(f"[USER CLEANUP] Checking ProjectUsers table...")
        project_users = list(ProjectUsers.uid_index.query(uid))
        if project_users:
            for pu in project_users:
                try:
                    pu.delete()
                    results["deleted"].append(f"ProjectUsers: {pu.name}")
                    print(f"[USER CLEANUP] ✓ Deleted ProjectUsers: {pu.name}")
                except Exception as delete_err:
                    print(f"[USER CLEANUP] ✗ Failed to delete ProjectUsers {pu.name}: {str(delete_err)}")
                    results["errors"].append(f"ProjectUsers.{pu.name}: {str(delete_err)}")
        else:
            results["not_found"].append("ProjectUsers")
            print(f"[USER CLEANUP] ○ No data in ProjectUsers")
    except Exception as e:
        print(f"[USER CLEANUP] ✗ Error querying ProjectUsers: {str(e)}")
        results["errors"].append(f"ProjectUsers: {str(e)}")
    
    # 2. Delete from ClinicJobs (scan for uid or validatorSub)
    try:
        print(f"[USER CLEANUP] Checking ClinicJobs table...")
        jobs = list(ClinicJobs.scan(ClinicJobs.uid == uid))
        if jobs:
            for job in jobs:
                try:
                    job.delete()
                    results["deleted"].append(f"ClinicJobs: {job.job_id}")
                    print(f"[USER CLEANUP] ✓ Deleted ClinicJobs: {job.job_id}")
                except Exception as delete_err:
                    print(f"[USER CLEANUP] ✗ Failed to delete ClinicJobs {job.job_id}: {str(delete_err)}")
                    results["errors"].append(f"ClinicJobs.{job.job_id}: {str(delete_err)}")
        else:
            results["not_found"].append("ClinicJobs")
            print(f"[USER CLEANUP] ○ No data in ClinicJobs")
    except Exception as e:
        print(f"[USER CLEANUP] ✗ Error querying ClinicJobs: {str(e)}")
        results["errors"].append(f"ClinicJobs: {str(e)}")
    
    # 3. Delete from ClinicalAnnotations (scan for uid)
    try:
        print(f"[USER CLEANUP] Checking ClinicalAnnotations table...")
        annotations = list(ClinicalAnnotations.scan(ClinicalAnnotations.uid == uid))
        if annotations:
            for annot in annotations:
                try:
                    annot.delete()
                    results["deleted"].append(f"ClinicalAnnotations: {annot.annotation_name}")
                    print(f"[USER CLEANUP] ✓ Deleted ClinicalAnnotations: {annot.annotation_name}")
                except Exception as delete_err:
                    print(f"[USER CLEANUP] ✗ Failed to delete ClinicalAnnotations {annot.annotation_name}: {str(delete_err)}")
                    results["errors"].append(f"ClinicalAnnotations.{annot.annotation_name}: {str(delete_err)}")
        else:
            results["not_found"].append("ClinicalAnnotations")
            print(f"[USER CLEANUP] ○ No data in ClinicalAnnotations")
    except Exception as e:
        print(f"[USER CLEANUP] ✗ Error querying ClinicalAnnotations: {str(e)}")
        results["errors"].append(f"ClinicalAnnotations: {str(e)}")
    
    # 4. Delete from ClinicalVariants (scan for uid or validatorSub)
    try:
        print(f"[USER CLEANUP] Checking ClinicalVariants table...")
        variants = list(ClinicalVariants.scan(ClinicalVariants.uid == uid))
        if variants:
            for var in variants:
                try:
                    var.delete()
                    results["deleted"].append(f"ClinicalVariants: {var.collection_name}")
                    print(f"[USER CLEANUP] ✓ Deleted ClinicalVariants: {var.collection_name}")
                except Exception as delete_err:
                    print(f"[USER CLEANUP] ✗ Failed to delete ClinicalVariants {var.collection_name}: {str(delete_err)}")
                    results["errors"].append(f"ClinicalVariants.{var.collection_name}: {str(delete_err)}")
        else:
            results["not_found"].append("ClinicalVariants")
            print(f"[USER CLEANUP] ○ No data in ClinicalVariants")
    except Exception as e:
        print(f"[USER CLEANUP] ✗ Error querying ClinicalVariants: {str(e)}")
        results["errors"].append(f"ClinicalVariants: {str(e)}")
    
    # 5. Delete from JupyterInstances (query by uid as hash key)
    try:
        print(f"[USER CLEANUP] Checking JupyterInstances table...")
        instances = list(JupyterInstances.query(uid))
        if instances:
            for inst in instances:
                try:
                    inst.delete()
                    results["deleted"].append(f"JupyterInstances: {inst.instanceName}")
                    print(f"[USER CLEANUP] ✓ Deleted JupyterInstances: {inst.instanceName}")
                except Exception as delete_err:
                    print(f"[USER CLEANUP] ✗ Failed to delete JupyterInstances {inst.instanceName}: {str(delete_err)}")
                    results["errors"].append(f"JupyterInstances.{inst.instanceName}: {str(delete_err)}")
        else:
            results["not_found"].append("JupyterInstances")
            print(f"[USER CLEANUP] ○ No data in JupyterInstances")
    except Exception as e:
        print(f"[USER CLEANUP] ✗ Error querying JupyterInstances: {str(e)}")
        results["errors"].append(f"JupyterInstances: {str(e)}")
    
    # 6. Delete from SavedQueries (query by uid as hash key)
    try:
        print(f"[USER CLEANUP] Checking SavedQueries table...")
        queries = list(SavedQueries.query(uid))
        if queries:
            for query in queries:
                try:
                    query.delete()
                    results["deleted"].append(f"SavedQueries: {query.name}")
                    print(f"[USER CLEANUP] ✓ Deleted SavedQueries: {query.name}")
                except Exception as delete_err:
                    print(f"[USER CLEANUP] ✗ Failed to delete SavedQueries {query.name}: {str(delete_err)}")
                    results["errors"].append(f"SavedQueries.{query.name}: {str(delete_err)}")
        else:
            results["not_found"].append("SavedQueries")
            print(f"[USER CLEANUP] ○ No data in SavedQueries")
    except Exception as e:
        print(f"[USER CLEANUP] ✗ Error querying SavedQueries: {str(e)}")
        results["errors"].append(f"SavedQueries: {str(e)}")
    
    # 7. Delete from CliUpload (query by uid as hash key)
    try:
        print(f"[USER CLEANUP] Checking CliUpload table...")
        uploads = list(CliUpload.query(uid))
        if uploads:
            for upload in uploads:
                try:
                    upload.delete()
                    results["deleted"].append(f"CliUpload: {upload.upload_id}")
                    print(f"[USER CLEANUP] ✓ Deleted CliUpload: {upload.upload_id}")
                except Exception as delete_err:
                    print(f"[USER CLEANUP] ✗ Failed to delete CliUpload {upload.upload_id}: {str(delete_err)}")
                    results["errors"].append(f"CliUpload.{upload.upload_id}: {str(delete_err)}")
        else:
            results["not_found"].append("CliUpload")
            print(f"[USER CLEANUP] ○ No data in CliUpload")
    except Exception as e:
        print(f"[USER CLEANUP] ✗ Error querying CliUpload: {str(e)}")
        results["errors"].append(f"CliUpload: {str(e)}")
    
    # 8. Delete from UserInfo (get by uid as hash key)
    try:
        print(f"[USER CLEANUP] Checking UserInfo table...")
        user_info = UserInfo.get(uid)
        user_info.delete()
        results["deleted"].append("UserInfo")
        print(f"[USER CLEANUP] ✓ Deleted UserInfo")
    except UserInfo.DoesNotExist:
        results["not_found"].append("UserInfo")
        print(f"[USER CLEANUP] ○ No data in UserInfo")
    except Exception as e:
        print(f"[USER CLEANUP] ✗ Error deleting UserInfo: {str(e)}")
        results["errors"].append(f"UserInfo: {str(e)}")
    
    # 9. Delete from Quota (get by uid as hash key)
    try:
        print(f"[USER CLEANUP] Checking Quota table...")
        quota = Quota.get(uid)
        quota.delete()
        results["deleted"].append("Quota")
        print(f"[USER CLEANUP] ✓ Deleted Quota")
    except Quota.DoesNotExist:
        results["not_found"].append("Quota")
        print(f"[USER CLEANUP] ○ No data in Quota")
    except Exception as e:
        print(f"[USER CLEANUP] ✗ Error deleting Quota: {str(e)}")
        results["errors"].append(f"Quota: {str(e)}")
    
    # 10. Delete from UserRole (query by uid as hash key)
    try:
        print(f"[USER CLEANUP] Checking UserRole table...")
        user_roles = list(UserRole.query(uid))
        if user_roles:
            for ur in user_roles:
                try:
                    ur.delete()
                    results["deleted"].append(f"UserRole: {ur.role_id}")
                    print(f"[USER CLEANUP] ✓ Deleted UserRole: {ur.role_id}")
                except Exception as delete_err:
                    print(f"[USER CLEANUP] ✗ Failed to delete UserRole {ur.role_id}: {str(delete_err)}")
                    results["errors"].append(f"UserRole.{ur.role_id}: {str(delete_err)}")
        else:
            results["not_found"].append("UserRole")
            print(f"[USER CLEANUP] ○ No data in UserRole")
    except Exception as e:
        print(f"[USER CLEANUP] ✗ Error querying UserRole: {str(e)}")
        results["errors"].append(f"UserRole: {str(e)}")
    
    print(f"[USER CLEANUP] Completed cleanup for user: {uid}")
    print(f"[USER CLEANUP] Summary - Deleted: {len(results['deleted'])}, Not Found: {len(results['not_found'])}, Errors: {len(results['errors'])}")
    
    return results
