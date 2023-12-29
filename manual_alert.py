
from pydantic import BaseModel, Field
from typing import List, Dict
import streamlit as st
from streamlit import session_state as ss
import streamlit_pydantic as sp
import yaml
from prom_selector import list_all_namespaces, get_prometheus_rule_selector


def display_rule_selectors(namespace, name, selector):
    st.markdown(f"Rule selector detected in **Namespace**: {namespace} **Name**: {name}")
    ss.add_rule_selector = st.toggle(key="key_rule_label", label=f'Add Selectors: {selector["matchLabels"]}', value=True)
    if ss.add_rule_selector:
        ss.rule_labels = selector["matchLabels"]
    else:
        ss.rule_labels = {}

def display_namespace_selectors(namespace, name, selector):
    st.markdown(f"Namespace selector detected in **Namespace**: {namespace} **Name**: {name}")
    ss.add_namespace_selector = st.toggle(key="key_rule_namespace", label=f'Add Selectors: {selector["matchLabels"]}', value=True)
    if ss.add_namespace_selector:
        inner_dict = selector.get('matchLabels', {})
        ss.namespace_labels = {"namespace": next(iter(inner_dict.values()), None)}
        st.markdown(f"Make sure you add **{list(inner_dict.keys())[0]} : {list(inner_dict.values())[0]}** to your {namespace}")
    else:
        ss.namespace_labels = {}


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
    initializer = [("cluster_detected", False), ("rule_selectors", {}), ("rule_namespace_selector", {}), ("namespaces", []), ("rule_labels", {}), ("namespace_labels", {}), ("generated_yaml", "")]
    for (name,value) in initializer:
        if name not in ss:
            ss[name] = value

    
    st.title("Prometheus Rule Editor")                  
    add_alert()

    
    
    if ss.cluster_detected == False:
        ss.namespaces = list_all_namespaces()

    if ss.rule_selectors == {} and ss.rule_namespace_selector == {} and len(ss.namespaces) != 0:

        ss.rule_selectors, ss.rule_namespace_selector = get_prometheus_rule_selector(ss.namespaces)

        # for (namespace, name), namespace_selector in ss.rule_namespace_selector.items():
        #     print(f"Namespace: {namespace}, Operator: {name}, Rule Selector: {namespace_selector}")
    else:
        for (namespace, name), selector in ss.rule_selectors.items():
            if len(selector) != 0:
                # st.toast("Rule Selector Detected", icon="🕵️")
                display_rule_selectors(namespace, name, selector)
                
        for (namespace, name), ns_selector in ss.rule_namespace_selector.items():
            if len(ns_selector) != 0:
                display_namespace_selectors(namespace, name, ns_selector)

    generate_button = st.button("Generate", on_click=generate_prometheus_rule)
    if ss.generated_yaml:
        st.code(body=ss.generated_yaml, language="yaml")

if __name__ == "__main__":
    main()