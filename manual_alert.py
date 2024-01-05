
from pydantic import BaseModel, Field
from typing import List, Dict
import streamlit as st
from streamlit import session_state as ss
import yaml
from kubernetes import client, config
from prom_selector import get_all_namespaces, get_all_operators, get_namespace_labels, get_operator_selectors
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
    custom_objects_client = client.CustomObjectsApi()
    initializer = [("cluster_detected", False), ("rule_selectors", {}), ("rule_namespace_selector", {}), ("namespaces", []), ("rule_labels", {}), ("namespace_labels", {}), ("generated_yaml", {}), ("get_operators", {}), ("no_ns_label", "")]
    for (name,value) in initializer:
        if name not in ss:
            ss[name] = value
    
    st.title("PrometheusRule Generator")                  
    add_alert()

    # Initialize session state variables
    if 'selected_operator' not in ss:
        ss.selected_operator = None
    if 'operators_initialized' not in ss:
        ss.operators_initialized = False

    if not ss.operators_initialized:
        ss.namespaces = get_all_namespaces(v1_client)
        ss.all_operators = get_all_operators(ss.namespaces, custom_objects_client)
        ss.operators_initialized = True

        # Auto-select the first operator, if available
        for namespace, operators in ss.all_operators.items():
            if operators:
                ss.selected_operator_name = operators[0]['metadata']['name']
                ss.selected_namespace = namespace
                ss.selected_operator = operators[0]
                get_operator_selectors(namespace, operators[0], v1_client)
                break
    else:
        get_operator_selectors(ss.selected_namespace, ss.selected_operator, v1_client)
    if ss.no_ns_label:
        st.warning(f"Please add the label {ss.no_ns_label} to atleast one namespace")


    # Sidebar: List namespaces and operators
    with st.sidebar:
        st.title("Namespaces and Operators")
        for namespace, operators in ss.all_operators.items():
            if operators:
                with st.expander(namespace):
                    for operator in operators:
                        op_name = operator['metadata']['name']
                        if st.button(op_name, key=f"{namespace}_{op_name}"):
                            ss.selected_operator_name = op_name
                            ss.selected_operator = operator
                            ss.selected_namespace = namespace
                            get_operator_selectors(namespace, operator, v1_client)
                            

    # Show warning if no operators are detected
    if not ss.selected_operator:
        st.warning("No operators detected.")
        # Display default rule generator page

    # Main area: Display information based on the selection
    if ss.selected_operator:
        st.write(f"You have selected operator: {ss.selected_operator_name} in namespace {ss.selected_namespace}")
        # Integrate rule generation with selected operator
        # generate_prometheus_rule(ss.selected_namespace, ss.rule_labels)
        # generate_prometheus_rule()


    
    if ss.cluster_detected == False:
        ss.namespaces = get_all_namespaces(v1_client)

    if ss.get_operators == False:
        ss.get_operators = get_all_operators(ss.namespaces)

    generate_button = st.button("Generate", on_click=generate_prometheus_rule)
    if generate_button:
        st.code(body=ss.generated_yaml, language="yaml")



if __name__ == "__main__":

    main()