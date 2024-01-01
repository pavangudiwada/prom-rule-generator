from kubernetes import client, config
import time
import streamlit as st
from streamlit import session_state as ss



def get_all_namespaces(v1_client):

    try:
        namespaces = v1_client.list_namespace() # Get all the namespaces
        ss.cluster_detected = True
    
    except Exception as e:
        print(f"An error occured while detecting namespaces: {e}")

    return [namespace.metadata.name for namespace in namespaces.items] # For each namespaces in the list of namespaces get the name found in metadata.name

def get_all_operators(namespaces, custom_objects_client):

    all_operators = {}

    for namespace in namespaces:
        try:
            prometheus_operator = custom_objects_client.list_namespaced_custom_object(
                group="monitoring.coreos.com",
                version="v1",
                namespace=namespace,
                plural="prometheuses"
            )

            if prometheus_operator['items']:

                all_operators[namespace] = prometheus_operator['items']
            
        except Exception as e:
            print(f"An error occurred in namespace {namespace}: {e}")

    return all_operators




def get_prometheus_rule_selector(namespaces, custom_objects_client):
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

    return rule_selectors, rule_namespace_selector

def get_namespace_labels(namespace, v1_client):

    try:
        ns = v1_client.read_namespace(name=namespace)
        return ns.metadata.labels
    except client.exceptions.ApiException as e:
        print(f"An error occurred: {e}")
        return None


def get_all_namespace_labels(v1_client):

    try:
        all_labels = {}
        for namespace in ss.namespaces:
            ns_labels = get_namespace_labels(namespace, v1_client)

            if ns_labels:
                all_labels.update()
        return all_labels
    except Exception as e:
        print(f"Exception {e} occured while getting all namespace labels")


def get_operator_selectors(namespace, operator, v1_client):
    try:
        rule_labels = operator.get('spec', {}).get('ruleSelector', {})
        namespace_labels = operator.get('spec', {}).get('ruleNamespaceSelector', {})
        if rule_labels:
            ss.rule_labels = rule_labels["matchLabels"]
        if namespace_labels:
            inner_dict = namespace_labels.get('matchLabels', {})
            ss.namespace_labels = {"namespace": next(iter(inner_dict.values()), None)}     

        all_labels = get_all_namespace_labels(v1_client)
        if inner_dict.items() not in all_labels.items():

            st.warning(f"Please add the label {inner_dict} to atleast one namespace")

    except Exception as e:
        print(f"An error {e} occured while getting operator selectors")

