import requests
import json

def get_access_token():
    post_data = {'client_id': sp_app_id,
        'scope': 'https://graph.microsoft.com/.default',
        'client_secret' : client_secret,
        'grant_type':'client_credentials'}
    initial_header = {'Content-type': 'application/x-www-form-urlencoded'}
    response = requests.post(f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token", data=post_data, headers=initial_header).json()
    return response.get("access_token")

def find_current_groups_in_ea(sp_object_id):
    temp_list = []
    header = {"Authorization": f"Bearer {token}",
              'ConsistencyLevel': 'eventual'}
    
    group_count = requests.get(f"{base_url}/servicePrincipals/{sp_object_id}/appRoleAssignedTo/$count", headers=header)
    group_count = int(group_count.json()) + 50
    response = requests.get(
        f"{base_url}/servicePrincipals/{sp_object_id}/appRoleAssignedTo?$top={group_count}", headers=header)
    if response.status_code == 200:
        for grp in response.json().get("value"):
            temp_list.append({"groupName": grp.get("principalDisplayName"),
                          "groupId": grp.get("principalId"),
                          "assignmentId": grp.get("id")
                          })
    return temp_list

def add_group_to_ea(id):
    header = {"Authorization": f"Bearer {token}",
              'Content-type': 'application/json'}
    post_data = {
        "principalId": id,
        "resourceId": sp_object_id,
        "appRoleId": app_role_id
    }
    response = requests.post(
        f"{base_url}/servicePrincipals/{sp_object_id}/appRoleAssignedTo", headers=header, json=post_data).json()
    print(response)

if __name__ == "__main__":
    sp_app_id = "<apn-app-id>" # SPN app id
    tenant_id = "<azure-tenant-id>" #  Tenant id
    client_secret = "<azure-client-secret>" # SP creds
    sp_object_id = "<sp-opject-id>" # SPN resource id
    app_role_id = "<sp-app-role-id>"  # EA appRole id
    base_url = "https://graph.microsoft.com/v1.0"


    old_ea_app_ids = ["app-id-1","app-id-2"]
    token = get_access_token()
    header = {"Authorization": f"Bearer {token}"}
    nested_list = []

    for ea_app in old_ea_app_ids : 
        all_entities= find_current_groups_in_ea(ea_app)
        nested_list.append(all_entities)

    identities = [item for sub_list in nested_list for item in sub_list]

    existing_groups_list = [d.get('groupName') for d in identities]
    with open("groups.json", "w") as f:
        f.write(json.dumps(list(existing_groups_list), indent=2))

    unique_groups = [i for n, i in enumerate(identities) if i not in identities[n + 1:]]
    for grp in unique_groups : 
        add_group_to_ea(grp.get("groupId"))
