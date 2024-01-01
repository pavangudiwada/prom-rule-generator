
from pydantic import BaseModel, Field
from typing import List, Dict
import streamlit as st
from streamlit import session_state as ss
# import streamlit_pydantic as sp
import yaml
from kubernetes import client, config
from prom_selector import get_all_namespaces, get_all_operators, get_namespace_labels, get_operator_selectors
import streamlit_antd_components as sac


def generate_prometheus_rule():
    template = {
        'apiVersion': 'monitoring.coreos.com/v1',
        'kind': 'PrometheusRule',
        'metadata': {
            'name': ss.alert,
            **ss.namespace_labels,
            'labels': {
                'role': 'alert-rules',
                **ss.rule_labels,
            },
        },
        'spec': {
            'groups': [{
                'name': f'{ss.alert}-rules',
                'rules': [{
                    'alert': f'{ss.alert}Alert',
                    'expr': f"{ss.expr}",
                    'for': ss.for_duration,
                    'labels': {
                        'severity': ss.severity,
                    },
                    'annotations': {
                        'summary': ss.summary,
                    },
                }],
            }],
        }
    }

    ss.generated_yaml = yaml.dump(template, sort_keys=False)


    
def add_alert():
    ss.alert = st.text_input(label="Alert Name")
    ss.expr = st.text_input(label="PromQL expression")
    ss.for_duration = st.text_input(label="For duration")
    ss.severity = st.selectbox("Pick one", ["critical", "warning", "info"])
    ss.summary = st.text_input(label="Summary", value=f"Alert for {ss.alert}")



def main():
    config.load_kube_config()

    v1_client = client.CoreV1Api()
    custom_objects_client = client.CustomObjectsApi()
    initializer = [("cluster_detected", False), ("rule_selectors", {}), ("rule_namespace_selector", {}), ("namespaces", []), ("rule_labels", {}), ("namespace_labels", {}), ("generated_yaml", ""), ("get_operators", {})]
    for (name,value) in initializer:
        if name not in ss:
            ss[name] = value
    
    st.title("Prometheus Rule Editor")                  
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
                ss.selected_operator = operators[0]['metadata']['name']
                ss.selected_namespace = namespace
                get_operator_selectors(namespace, operators[0], v1_client)
                break

    # Sidebar: List namespaces and operators
    with st.sidebar:
        st.title("Namespaces and Operators")
        for namespace, operators in ss.all_operators.items():
            if operators:
                with st.expander(namespace):
                    for op in operators:
                        op_name = op['metadata']['name']
                        if st.button(op_name, key=f"{namespace}_{op_name}"):
                            ss.selected_operator = op_name
                            ss.selected_namespace = namespace
                            get_operator_selectors(namespace, op, v1_client)
                            # ss.rule_labels = get_namespace_labels(namespace, v1_client)  # Fetch labels for the selected namespace

    # Show warning if no operators are detected
    if not ss.selected_operator:
        st.warning("No operators detected.")
        # Display default rule generator page

    # Main area: Display information based on the selection
    if ss.selected_operator:
        st.write(f"You have selected operator: {ss.selected_operator} in namespace {ss.selected_namespace}")
        # Integrate rule generation with selected operator
        # generate_prometheus_rule(ss.selected_namespace, ss.rule_labels)
        generate_prometheus_rule()



















    # def
    
    if ss.cluster_detected == False:
        ss.namespaces = get_all_namespaces(v1_client)

    if ss.get_operators == False:
        ss.get_operators = get_all_operators(ss.namespaces)

    else:
        for operator in ss.get_operators.values():
            print(operator)
            

    # if ss.rule_selectors == {} and ss.rule_namespace_selector == {} and len(ss.namespaces) != 0:
    #     ss.rule_selectors, ss.rule_namespace_selector = get_prometheus_rule_selector(ss.namespaces)

    # else:
    #     for (namespace, name), selector in ss.rule_selectors.items():
    #         if len(selector) != 0:
    #             display_rule_selectors(namespace, name, selector)
                
    #     for (namespace, name), ns_selector in ss.rule_namespace_selector.items():
    #         if len(ns_selector) != 0:
    #             display_namespace_selectors(namespace, name, ns_selector)

    generate_button = st.button("Generate", on_click=generate_prometheus_rule)
    if ss.generated_yaml:
        st.code(body=ss.generated_yaml, language="yaml")








if __name__ == "__main__":

    main()