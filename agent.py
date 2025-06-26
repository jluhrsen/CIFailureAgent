#!/usr/bin/env python3
import os, sys, asyncio

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

async def main():
    api_key = os.getenv("API_KEY")
    if not api_key:
        print("ERROR: set API_KEY in env", file=sys.stderr)
        sys.exit(1)

    client = OpenAIChatCompletionClient(model="gpt-4o", api_key=api_key)
    agent  = AssistantAgent(name="CIFailureAgent", model_client=client)

    # Hard-coded failure title + log snippet:
    # from this job https://prow.ci.openshift.org/view/gs/test-platform-results/logs/periodic-ci-openshift-release-master-ci-4.20-upgrade-from-stable-4.19-e2e-aws-ovn-upgrade/1938135592197951488
    failure_title = "[sig-network] Services should be rejected for evicted pods (no endpoints exist) [Suite:openshift/conformance/parallel] [Suite:k8s]"
    failure_log = """
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

    prompt = (
        "I have a failed CI test.  \n"
        f"**Test name:** {failure_title}  \n"
        "**Pod spec + status snippet:**\n"
        f"{failure_log}\n\n"
        "Please read the log snippet above and suggest 3 plausible root causes for why this test might have failed."
    )

    result = await agent.run(task=prompt)
    print("\n=== GPT-4o Analysis ===\n")
    print(result.messages[-1].content)
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
