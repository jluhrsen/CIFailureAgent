#!/usr/bin/env python3
import os, sys, asyncio

from autogen import AssistantAgent, UserProxyAgent
from autogen.coding import LocalCommandLineCodeExecutor
import tempfile
from autogen.agentchat import register_function # Keep this import

async def parse_failure():
    headline = "[sig-network] Services should be rejected for evicted pods (no endpoints exist) [Suite:openshift/conformance/parallel] [Suite:k8s]"
    logs = """
        {  terminationMessagePath: /dev/termination-log
                terminationMessagePolicy: File
                volumeMounts:
                - mountPath: /var/run/secrets/kubernetes.io/serviceaccount
                  name: kube-api-access-7kqtx
                  readOnly: true
              dnsPolicy: ClusterFirst
              enableServiceLinks: true
              imagePullSecrets:
              - name: default-dockercfg-zlv2s
              nodeName: ip-10-0-87-6.us-east-2.compute.internal
              preemptionPolicy: PreemptLowerPriority
              priority: 0
              restartPolicy: Always
              schedulerName: default-scheduler
              securityContext: {}
              serviceAccount: default
              serviceAccountName: default
              terminationGracePeriodSeconds: 0
              tolerations:
              - effect: NoExecute
                key: node.kubernetes.io/not-ready
                operator: Exists
                tolerationSeconds: 300
              - effect: NoExecute
                key: node.kubernetes.io/unreachable
                operator: Exists
                tolerationSeconds: 300
              volumes:
              - name: kube-api-access-7kqtx
                projected:
                  defaultMode: 420
                  sources:
                  - serviceAccountToken:
                      expirationSeconds: 3607
                      path: token
                  - configMap:
                      items:
                      - key: ca.crt
                        path: ca.crt
                      name: kube-root-ca.crt
                  - downwardAPI:
                      items:
                      - fieldRef:
                          apiVersion: v1
                          fieldPath: metadata.namespace
                        path: namespace
                  - configMap:
                      items:
                      - key: service-ca.crt
                        path: service-ca.crt
                      name: openshift-service-ca.crt
            status:
              conditions:
              - lastProbeTime: null
                lastTransitionTime: "2025-06-26T10:04:14Z"
                status: "True"
                type: PodReadyToStartContainers
              - lastProbeTime: null
                lastTransitionTime: "2025-06-26T10:04:09Z"
                status: "True"
                type: Initialized
              - lastProbeTime: null
                lastTransitionTime: "2025-06-26T10:04:14Z"
                status: "True"
                type: Ready
              - lastProbeTime: null
                lastTransitionTime: "2025-06-26T10:04:14Z"
                status: "True"
                type: ContainersReady
              - lastProbeTime: null
                lastTransitionTime: "2025-06-26T10:04:09Z"
                status: "True"
                type: PodScheduled
              containerStatuses:
              - containerID: cri-o://e7b51de37763373cad1b35de513253e8836f66654eaa59821dbdf7bd849df72b
                image: quay.io/openshift/community-e2e-images:e2e-1-registry-k8s-io-e2e-test-images-agnhost-2-53-S5hiptYgC5MyFXZH
                imageID: quay.io/openshift/community-e2e-images@sha256:1c5d47ecd9c4fca235ec0eeb9af0c39d8dd981ae703805a1f23676a9bf47c3bb
                lastState: {}
                name: evicted-pod
                ready: true
                restartCount: 0
                started: true
                state:
                  running:
                    startedAt: "2025-06-26T10:04:11Z"
                volumeMounts:
                - mountPath: /var/run/secrets/kubernetes.io/serviceaccount
                  name: kube-api-access-7kqtx
                  readOnly: true
                  recursiveReadOnly: Disabled
              hostIP: 10.0.87.6
              hostIPs:
              - ip: 10.0.87.6
              phase: Running
              podIP: 10.128.3.89
              podIPs:
              - ip: 10.128.3.89
              qosClass: BestEffort
              startTime: "2025-06-26T10:04:09Z"}
        """

    print("\n--- Executing parse_failure() ---")
    return f"Headline:\n{headline}\n\nLogs:\n{logs}"

async def main():
    api_key = os.getenv("API_KEY")
    if not api_key:
        print("ERROR: set API_KEY in env.", file=sys.stderr)
        sys.exit(1)

    code_executor = LocalCommandLineCodeExecutor(
        timeout=60,
        work_dir=tempfile.TemporaryDirectory().name,
    )

    llm_config = {
        "config_list": [
            {
                "model": "gpt-4o",
                "api_key": api_key,
            }
        ],
    }

    assistant = AssistantAgent(
        name="CIFailureAgent",
        llm_config=llm_config,
        system_message=(
            "You are a helpful AI assistant tasked with analyzing OpenShift CI job failures. "
            "You have access to a tool named `parse_failure` to retrieve failure details. "
            "Always call the `parse_failure` **tool** first when asked about a CI job failure. "
            "After retrieving details, analyze them and suggest **3 plausible root causes**. "
            "Conclude your response by listing the root causes under the heading 'Plausible Root Causes:'."
        ),
    )

    user_proxy = UserProxyAgent(
        name="UserProxy",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=10,
        code_execution_config={"executor": code_executor},
        is_termination_msg=lambda x: isinstance(x, dict) and x.get("content") is not None and "Plausible Root Causes:" in x["content"],
    )

    register_function(
        parse_failure,
        caller=assistant,
        executor=user_proxy,
        name="parse_failure",
        description="Returns hard-coded CI failure headline and logs for analysis."
    )

    prompt = (
        "An OpenShift CI job has failed. Please analyze the failure details by using the "
        "`parse_failure` tool, and then suggest **3 plausible root causes**. "
        "Format your final response by listing them under the heading 'Plausible Root Causes:'."
    )

    print("--- Starting chat with Tool Use ---")
    chat_result = await user_proxy.a_initiate_chat(
        assistant,
        message=prompt,
        max_turns=7
    )

    print("\n=== CIFailureAgent Analysis ===\n")
    print(chat_result.summary)

if __name__ == "__main__":
    asyncio.run(main())
