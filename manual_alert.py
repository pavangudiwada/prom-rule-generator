
from pydantic import BaseModel, Field
from typing import List, Dict
import streamlit as st
from streamlit import session_state as ss
import streamlit_pydantic as sp
import yaml


def generate_prometheus_rule():
    template = {
        'apiVersion': 'monitoring.coreos.com/v1',
        'kind': 'PrometheusRule',
        'metadata': {
            'name': ss.alert,
            'labels': {
                'role': 'alert-rules',
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
                        'summary': f'Alert for {ss.alert}',
                    },
                }],
            }],
        }
    }

    generated_yaml = yaml.dump(template, sort_keys=False)
    st.text_area("Generated YAML", value=generated_yaml, height=500)

def add_alert():
    ss.alert = st.text_input(label="Alert Name")
    ss.expr = st.text_input(label="PromQL expression")
    ss.for_duration = st.text_input(label="For Duration")
    ss.severity = st.selectbox("Pick one", ["critical", "warning", "info"])
    ss.summary = st.text_input(label="Summary", value=f"This alert uses {ss.alert}")


def main():
    st.title("Prometheus Rule Editor")
    add_alert()

    st.button("Generate", on_click=generate_prometheus_rule)


if __name__ == "__main__":
    main()
