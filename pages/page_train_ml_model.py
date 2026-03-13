from azure.ai.ml import MLClient, command
from azure.identity import DefaultAzureCredential
import streamlit as st
import os


subscription_id= "d2bda5a8-0cf7-480c-bf1f-6d7ec7b665ba"
resource_group = "PerceptBootcamp-aia-Norway"
workspace_name = "percept-workspace"
compute="D4s-v3-cpu694450"

# 1. Connect to Azure ML Workspace
ml_client = MLClient(DefaultAzureCredential(), 
                     subscription_id=subscription_id, 
                     rg=resource_group, 
                     workspace=workspace_name
                     )

st.title("ML Control Center")
lr = st.slider("Learning Rate", 0.01, 0.5)

# 1. Get the absolute path of the directory where your Web App code lives
# In Azure Web Apps, this is usually /home/site/wwwroot
base_dir = os.path.abspath(os.path.dirname(__file__))
code_dir = os.path.join(base_dir, "src")

if st.button("Start Training Job"):
    # 2. Define the training task
    job = command(
        code=code_dir, 
        command="python lstm_train.py --lr ${{inputs.learning_rate}}",
        inputs={"learning_rate": lr},
        environment="AzureML-sklearn-1.0-ubuntu20.04-py38-cpu@latest",
        compute=compute
    )
    
    # 3. Submit the job
    returned_job = ml_client.jobs.create_or_update(job)
    st.info(f"Job started! View here: {returned_job.services['Studio'].endpoint}")



