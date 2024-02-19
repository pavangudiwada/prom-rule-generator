
from pydantic import BaseModel, Field
from typing import List, Dict
import streamlit as st
from streamlit import session_state as ss
import yaml
from kubernetes import client, config
from kubernetes.dynamic import DynamicClient
from kubernetes.client.api_client import ApiClient
from prom_selector import get_all_namespaces, get_all_prometheuses, get_namespace_labels, get_prometheus_selectors
import streamlit_antd_components as sac


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
    ss.group_name = st.text_input(label="Group Name")
    ss.alert = st.text_input(label="Alert Name")
    ss.expr = st.text_input(label="PromQL expression")
    ss.for_duration = st.text_input(label="For duration")
    ss.severity = st.selectbox("Pick one", ["critical", "warning", "info"])
    ss.summary = st.text_input(label="Summary", value=f"Alert for {ss.alert}")
    ss.description = st.text_input(label="Description")



def main():
    config.load_kube_config()

    v1_client = client.CoreV1Api()
    k8s_client = ApiClient()

    custom_objects_client = client.CustomObjectsApi()
    initializer = [("cluster_detected", False), ("rule_selectors", {}), ("rule_namespace_selector", {}), ("namespaces", []), ("rule_labels", {}), ("namespace_labels", {}), ("generated_yaml", {}), ("get_prometheus", {}), ("no_ns_label", "")]
    for (name,value) in initializer:
        if name not in ss:
            ss[name] = value
    
    st.title("PrometheusRule Generator")                  
    add_alert()

    # Initialize session state variables
    if 'selected_prometheus' not in ss:
        ss.selected_prometheus = None
    if 'prometheus_initialized' not in ss:
        ss.prometheus_initialized = False

    if not ss.prometheus_initialized:
        ss.namespaces = get_all_namespaces(v1_client)
        ss.all_prometheus = get_all_prometheuses(ss.namespaces, custom_objects_client)
        ss.prometheus_initialized = True

        # Auto-select the first prometheus, if available
        for namespace, prometheus in ss.all_prometheus.items():
            if prometheus:
                ss.selected_prometheus_name = prometheus[0]['metadata']['name']
                ss.selected_namespace = namespace
                ss.selected_prometheus = prometheus[0]
                get_prometheus_selectors(namespace, prometheus[0], v1_client)
                break
    else:
        get_prometheus_selectors(ss.selected_namespace, ss.selected_prometheus, v1_client)
    if ss.no_ns_label:
        st.warning(f"Please add the label {ss.no_ns_label} to atleast one namespace")


    # Sidebar: List namespaces and prometheus
    with st.sidebar:
        st.title("Namespace and Prometheus")
        for namespace, prometheuses in ss.all_prometheus.items():
            if prometheuses:
                with st.expander(namespace):
                    for prometheus in prometheuses:
                        prom_name = prometheus['metadata']['name']
                        if st.button(prom_name, key=f"{namespace}_{prom_name}"):
                            ss.selected_prometheus_name = prom_name
                            ss.selected_prometheus = prometheus
                            ss.selected_namespace = namespace
                            get_prometheus_selectors(namespace, prometheus, v1_client)
                            

    # Show warning if no Prometheus CRD are detected
    if not ss.selected_prometheus:
        st.warning("No Prometheus CRD detected.")
        # Display default rule generator page

    # Main area: Display information based on the selection
    if ss.selected_prometheus:
        st.write(f"You have selected Prometheus: {ss.selected_prometheus_name} in namespace {ss.selected_namespace}") ## CHANGE TO MARKDOWN

    
    if ss.cluster_detected == False:
        ss.namespaces = get_all_namespaces(v1_client)

    if ss.get_prometheus == False:
        ss.get_prometheus = get_all_prometheuses(ss.namespaces)

    generate_button = st.button("Generate", on_click=generate_prometheus_rule)
    if generate_button:
        st.code(body=ss.generated_yaml, language="yaml")


if __name__ == "__main__":
    main()