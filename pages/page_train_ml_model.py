import streamlit as st
import os
import time
from azure.ai.ml import MLClient, command
from azure.identity import DefaultAzureCredential
from azure.ai.ml.entities import Environment, AmlCompute

# Safely handle the import
try:
    from azure.core.exceptions import AzureError
except ImportError:
    AzureError = Exception



subscription_id = "d2bda5a8-0cf7-480c-bf1f-6d7ec7b665ba" # os.getenv("AZURE_SUBSCRIPTION_ID")
resource_group = "perceptbootcamp-aia-norway" 
workspace_name = "percept-workspace"
compute_name = "Standard-D4s-v3-cluster-694450" #"Standard-DS3-v2-cluster-694450"  # D4s-v3-cpu694450 cpu not possible to use with command jobs, only clusters

# 1. Connect to Azure ML Workspace
ml_client = MLClient(DefaultAzureCredential(), 
                     subscription_id=subscription_id, 
                     rg=resource_group, 
                     workspace=workspace_name
                     )

st.title("ML Control Center")
hidden_nodes = st.slider("Number of neurons (hidden nodes)", 1, 5)

# 1. Get the absolute path of the directory where your Web App code lives
# In Azure Web Apps, this is usually /home/site/wwwroot
base_dir = os.path.abspath(os.path.dirname(__file__))
code_dir = os.path.join(base_dir, "src")
# 1. Point to your local env.yml (the one we rewrote for Python 3.8/TF 2.13)
# Assuming it's in your /src folder
conda_file_path = os.path.join(code_dir, "environment.yml")

# Use the environment variable Azure sets for the root of the site DID NOT WORK
#site_root = os.environ.get("HOME", "/home") + "/site/wwwroot"
#code_dir = os.path.join(site_root, "src")


if not os.path.exists(code_dir):
    # Fallback for local testing
    code_dir = os.path.abspath("./src")

st.write(f"Uploading code from: {code_dir}")
st.write(f"Code_dir content: {os.listdir(code_dir)}")
if st.button("Start Training Job"):
 
     # 2. Define the Environment object
    st.write(f"Creating environment using: {conda_file_path}")
    custom_env = Environment(
        name="lstm_training_env",
        description="Custom environment for LSTM training",
        # Use a reliable base image that always exists
        image="mcr.microsoft.com/azureml/openmpi4.1.0-ubuntu20.04:latest",
        conda_file=conda_file_path,
    )
    job = command(
        name=f"lstm-train-{int(time.time())}", # Add a unique name
        code=code_dir, 
        inputs={"hidden_nodes": hidden_nodes},
        command="python3 train_lstm.py --hidden_nodes 5", # ${{inputs.hidden_nodes}}",
        environment=custom_env, # "AzureML-sklearn-1.0-ubuntu20.04-py38-cpu@latest",
        compute=compute_name
    )
    ##### TEMPORARY code
    try:
        # Diagnostic: Let's see if the client can even "see" the compute
        found_compute = ml_client.compute.get(compute_name)
        st.success(f"✅ Found compute cluster: {found_compute.name} (Status: {found_compute.provisioning_state})")
        
        # 3. Build the job using the validated name
        #job = command(
        #    code="/tmp/8de84fcf8927f7a/pages/src",
        #    command="python3 train_lstm.py --hidden_nodes ${{inputs.hidden_nodes}}",
        #    inputs={"hidden_nodes": 1},
        #    environment=custom_env,
        #    compute=compute_name, # Use the string name we just verified
        #    experiment_name="lstm-training-webapp"
        #)

        #returned_job = ml_client.jobs.create_or_update(job)
        #st.success(f"🚀 Job submitted! Name: {returned_job.name}")

    except Exception as e:
        st.error(f"Error: {str(e)}")
        st.error(f"Failed to find {compute_name}")
        if "not found" in str(e).lower():
            st.warning("The SDK still can't find the cluster. Double-check that your Resource Group name in the code matches the 'perceptbootcamp...' spelling exactly.")
    ##### END TEMPORARY CODE
    
    try:
        st.info(f"Submitting job from: {code_dir}")
        st.write("Checking job attributes before submission...")
        # This line will tell us if any attribute is missing before we even send it
        st.json(job._to_dict())
        returned_job = ml_client.jobs.create_or_update(job)
        st.success(f"Job created! ID: {returned_job.name}")

    except Exception as e:
        st.error(f"### Job Submission Failed")
        
        # This is the most reliable way to show the error message in Python 3.12
        error_msg = str(e)
        st.code(error_msg)
        
        # Logical check for common issues
        if "AssetException" in error_msg or "upload" in error_msg.lower():
            st.warning("⚠️ **Diagnosis:** The SDK is failing to zip or upload the 'src' folder.")
            st.info("This usually happens because the Web App identity lacks 'Storage Blob Data Contributor' "
                    "permissions on the workspace storage account.")
            


