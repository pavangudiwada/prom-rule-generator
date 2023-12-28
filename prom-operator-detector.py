from kubernetes import client, config
import time
import streamlit as st
from streamlit import session_state as ss

def list_all_namespaces():

    # st.toast("Detected K8s Cluster", icon='☸️')

    config.load_kube_config()
    v1 = client.CoreV1Api()
    namespaces = v1.list_namespace() # Get all the namespaces

    ss.cluster_detected = True

    return [namespace.metadata.name for namespace in namespaces.items] # For each namespaces in the list of namespaces get the name found in metadata.name


def get_prometheus_rule_selector(namespaces):
    custom_objects_api = client.CustomObjectsApi()
    rule_selectors = {} # Collects all the Prometheus Operators and their rule selectors as a set (namespace, name)
    rule_namespace_selector = {}

    for namespace in namespaces: # Get the list of namespaces and try to find a prometheus operator 
        try: # This is like running kubectl get prometheuses
            prometheus_operators = custom_objects_api.list_namespaced_custom_object( 
                group="monitoring.coreos.com",
                version="v1",
                namespace=namespace,
                plural="prometheuses"
            )

            for item in prometheus_operators['items']: # There could be multiple operators, and items has a list of them
                name = item['metadata']['name']        # From the metadata part of each item, get its name
                rule_selector = item.get('spec', {}).get('ruleSelector', {})   # If spec or ruleSelector doesnt exist then {} is used instead of an exception
                rule_selectors[(namespace, name)] = rule_selector     # If there was a rule 

                rule_namespace = item.get('spec', {}).get('ruleNamespaceSelector', {})
                rule_namespace_selector[(namespace, name)] = rule_namespace

        except client.exceptions.ApiException as e:
            print(f"An error occurred in namespace {namespace}: {e}")
    # st.toast("Prometheus Operator Detected", icon="👌")

    return rule_selectors, rule_namespace_selector

# namespaces = list_all_namespaces()

# rule_selectors = get_prometheus_rule_selector(namespaces)
# for (namespace, name), selector in rule_selectors.items():
#     print(f"Namespace: {namespace}, Operator: {name}, Rule Selector: {selector}")

# def get_current_cluster_name():
#     # Load the kubeconfig file
#     config.load_kube_config()  # Use config.load_incluster_config() if running inside a cluster

#     # Get the current context
#     current_context = config.list_kube_config_contexts()[1]['context']

#     # The name of the current cluster
#     cluster_name = current_context['cluster']
#     return cluster_name

# # Example usage
# cluster_name = get_current_cluster_name()
# print(cluster_name)
