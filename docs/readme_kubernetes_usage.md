# MC Trade Sizing - Kubernetes Usage Guide (WSL2 Environment)

This guide explains how to run the **MC Trade Sizing** tool in a Kubernetes environment, especially when using **WSL2 on Windows** (e.g., Ubuntu via WSL2).

## Prerequisites

- WSL2 with a Linux distribution (e.g., Ubuntu)
- Kubernetes CLI (`kubectl`) installed and configured
- Kubernetes cluster up and running (e.g., via `minikube`, Docker Desktop, or a remote cluster)

---

## Starting the WSL2 Shell (Ubuntu)

You can open your Ubuntu (WSL2) environment in several ways:

### ✅ Option 1: Via PowerShell or CMD

```powershell
wsl -d Ubuntu
```

> Use `wsl -l -v` to list available distributions if you're unsure of the exact name.

### ✅ Option 2: Via Windows Terminal

Open the Windows Terminal and choose the “Ubuntu” profile from the tab menu (only available if installed with WSL2).

### ✅ Option 3: From the Start Menu

Type “Ubuntu” in the Start Menu and launch the app.

---

## Basic Checks Inside Ubuntu

Run the following commands to verify that your WSL and Python environment is functioning:

```bash
whoami        # Shows your WSL username
uname -r      # Shows the Linux kernel (WSL2 includes "microsoft")
which python3 # Should return something like /usr/bin/python3
```

---

## Kubernetes Commands for MC Trade Sizing

### 1. Apply the Kubernetes Job

```bash
kubectl apply -f k8s/dps-job.yaml
```

### 2. Check Job and Pod Status

```bash
kubectl get jobs
kubectl get pods
```

### 3. View Logs

```bash
kubectl logs -l job-name=mc-trade-simulation
```

### 4. Delete the Job

To reset or restart the job:

```bash
kubectl delete job mc-trade-simulation
```

> This also removes the associated pod.

### 5. Restart the Job

Re-apply the job definition (e.g., after code changes):

```bash
kubectl delete job mc-trade-simulation
kubectl apply -f k8s/dps-job.yaml
```

### 6. (Optional) Copy Results from the Pod

First, get the pod name:

```bash
kubectl get pods
```

Then copy files (e.g., results) from the pod to your local system:

```bash
kubectl cp <pod-name>:/app/results ./results
```

Replace `<pod-name>` with the actual pod name shown in the previous step.

---

## Notes

- Make sure your cluster has access to the container image used in `dps-job.yaml`.
- You may need to adapt volume mounts or imagePullPolicy if using a local or custom image.
- The image is designed to be self-contained and should not require manual setup inside the pod.

For advanced configurations or help, please consult your Kubernetes provider or CI/CD pipeline documentation.
