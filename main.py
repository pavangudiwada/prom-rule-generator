
from pydantic import BaseModel, Field
from typing import List, Dict
import streamlit as st
from streamlit import session_state as ss
import yaml
from kubernetes import client, config
from kubernetes.dynamic import DynamicClient
from kubernetes.client.api_client import ApiClient
from prom_selector import get_all_namespaces, get_all_prometheuses, get_namespace_labels,get_all_namespace_labels, get_prometheus_selectors
import streamlit_antd_components as sac
import time


def generate_prometheus_rule():
    template = {
        'apiVersion': 'monitoring.coreos.com/v1',
        'kind': 'PrometheusRule',
        'metadata': {
            'name': f"{ss.alert}-rule",
            **ss.namespace_labels,
            'labels': {
                'role': 'alert-rules',
                **ss.rule_labels,
            },
        },
        'spec': {
            'groups': [{
                'name': f'{ss.group_name}',
                'rules': [{
                    'alert': f'{ss.alert}',
                    'expr': f"{ss.expr}",
                    'for': ss.for_duration,
                    'labels': {
                        'severity': ss.severity,
                    },
                    'annotations': {
                        'summary': ss.summary,
                        'description' : ss.description,
                    },
                }],
            }],
        }
    }

    ss.generated_yaml = yaml.dump(template, sort_keys=False)


def add_alert():

    with st.form('prom-alert'):
        ss.group_name = st.text_input(label="Group Name: A group can have multiple alert rules in it")
        ss.alert = st.text_input(label="Alert Name: Ex: HighErrorRate")
        ss.expr = st.text_input(label="PromQL expression: If this conditon evaluates to true, the alert will fire")
        ss.for_duration = st.text_input(label="How long before the alert fires, once the PromQL condition is true? Ex: 5m - Five Minutes")
        ss.severity = st.selectbox("Choose a severity level", ["critical", "warning", "info"])
        ss.summary = st.text_input(label="Summary: ", value=f"This is an alert for {ss.alert}")
        ss.description = st.text_input(label="Description: [optional]")

        generate_button = st.form_submit_button("Generate", on_click=generate_prometheus_rule)
        if generate_button:
            mandatory_fields = [ss.group_name, ss.alert, ss.expr, ss.for_duration, ss.severity, ss.summary]
            if all(mandatory_fields):
                st.code(body=ss.generated_yaml, language="yaml")
            else:
                st.error("Please fill in all required fields.")


@st.cache_data
def get_name_and_namespace(prometheus):
    return prometheus[0]['metadata']['namespace'],prometheus[0]['metadata']['name']

def initialize_prometheus_instances(_v1_client, _custom_objects_client):

    ss.namespaces = get_all_namespaces(_v1_client)
    if 'initialized' not in ss or not ss.initialized:
        ss.all_prometheus = get_all_prometheuses(ss.namespaces, _custom_objects_client)
        ss.initialized = True  

def populate_sidebar_and_handle_selection(v1_client):
    if ss.all_prometheus:
        ss.prometheus_options = [f"{instance[0]['metadata']['namespace']}/{instance[0]['metadata']['name']}" for instance in ss.all_prometheus]

        current_selection = ss.get('selected_prometheus_option', ss.prometheus_options[0])
        selected_option = st.sidebar.selectbox("Prometheus Instances", ss.prometheus_options, index=ss.prometheus_options.index(current_selection))
        ss.namespace_labels, ss.rule_labels, ss.no_ns_label = get_prometheus_selectors(v1_client, ss.selected_namespace, ss.all_prometheus[0])
        
        if selected_option != current_selection:
            ss.selected_prometheus_option = selected_option
            selected_namespace, selected_prometheus_name = selected_option.split('/')

            for instance in ss.all_prometheus:
                if instance[0]['metadata']['namespace'] == selected_namespace and instance[0]['metadata']['name'] == selected_prometheus_name:
                    ss.selected_prometheus = instance
                    ss.selected_namespace = instance[0]['metadata']['namespace']
                    ss.selected_prometheus_name = instance[0]['metadata']['name']
                    
                    ss.namespace_labels, ss.rule_labels, ss.no_ns_label = get_prometheus_selectors(v1_client, ss.selected_namespace, ss.selected_prometheus)
    else:
        st.sidebar.write("No Prometheus instances found.")


def main():
    config.load_kube_config()

    v1_client = client.CoreV1Api()
    k8s_client = ApiClient()

    custom_objects_client = client.CustomObjectsApi()
    initializer = {
        "rule_selectors": {},
        "rule_namespace_selector": {},
        "namespaces": [],
        "rule_labels": {},
        "namespace_labels": {},
        "generated_yaml": {},
        "get_prometheus": {},
        "no_ns_label": "",
        "selected_prometheus": None,
        "prometheus_initialized": False, 
        "all_prometheus": [],
        "selected_namespace": None,
        "prometheus_options" : [],
        "initialized": False,
        "selected_prometheus_name": None

    }

    for name, value in initializer.items():
        ss.setdefault(name, value)

    
    st.title("PrometheusRule Generator")           
    if ss.selected_prometheus:
        st.markdown(f"Generate a PrometheusRule for **{ss.selected_prometheus_name}** in the namespace **{ss.selected_namespace}**")       
    add_alert()

    initialize_prometheus_instances(v1_client, custom_objects_client)
    populate_sidebar_and_handle_selection(v1_client) 

    if ss.no_ns_label:
        st.warning(f"Please add the label {ss.no_ns_label} to at least one namespace")

if __name__ == "__main__":
    main()