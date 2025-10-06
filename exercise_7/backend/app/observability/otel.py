"""
OpenTelemetry observability setup with Tracer, Metrics, and Exporter initialization
Includes span attributes for tool.name, retries, latency_ms, and status
"""

import os
import logging
from typing import Optional
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import ConsoleMetricExporter, PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

logger = logging.getLogger(__name__)

# Global observability state
_tracer_provider: Optional[TracerProvider] = None
_meter_provider: Optional[MeterProvider] = None
_is_initialized = False

def setup_observability(
    service_name: str = "exercise7-backend",
    service_version: str = "1.0.0",
    jaeger_endpoint: Optional[str] = None,
    enable_console_export: bool = True
) -> None:
    """
    Initialize OpenTelemetry observability stack
    
    Args:
        service_name: Name of the service
        service_version: Version of the service
        jaeger_endpoint: Jaeger collector endpoint (optional)
        enable_console_export: Whether to enable console exporters
    """
    global _tracer_provider, _meter_provider, _is_initialized
    
    if _is_initialized:
        logger.info("Observability already initialized")
        return
    
    logger.info("Initializing OpenTelemetry observability...")
    
    # Create resource with service information
    resource = Resource.create({
        "service.name": service_name,
        "service.version": service_version,
        "service.instance.id": os.getenv("HOSTNAME", "localhost"),
    })
    
    # Setup tracing
    _setup_tracing(resource, jaeger_endpoint, enable_console_export)
    
    # Setup metrics
    _setup_metrics(resource, enable_console_export)
    
    # Setup automatic instrumentation
    _setup_auto_instrumentation()
    
    _is_initialized = True
    logger.info("OpenTelemetry observability initialized successfully")

def _setup_tracing(
    resource: Resource, 
    jaeger_endpoint: Optional[str], 
    enable_console_export: bool
) -> None:
    """Setup tracing with span processors and exporters"""
    global _tracer_provider
    
    # Create tracer provider
    _tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(_tracer_provider)
    
    # Add console exporter for development
    if enable_console_export:
        console_exporter = ConsoleSpanExporter()
        console_processor = BatchSpanProcessor(console_exporter)
        _tracer_provider.add_span_processor(console_processor)
    
    # Add OTLP exporter for Jaeger if endpoint provided
    if jaeger_endpoint:
        try:
            otlp_exporter = OTLPSpanExporter(
                endpoint=jaeger_endpoint,
                insecure=True
            )
            otlp_processor = BatchSpanProcessor(otlp_exporter)
            _tracer_provider.add_span_processor(otlp_processor)
            logger.info(f"OTLP exporter configured: {jaeger_endpoint}")
        except Exception as e:
            logger.warning(f"Failed to setup OTLP exporter: {e}")
    
    # Add default OTLP exporter for local development
    try:
        default_otlp_exporter = OTLPSpanExporter(
            endpoint="http://otel-collector:4317",
            insecure=True
        )
        default_otlp_processor = BatchSpanProcessor(default_otlp_exporter)
        _tracer_provider.add_span_processor(default_otlp_processor)
        logger.info("Default OTLP exporter configured for otel-collector:4317")
    except Exception as e:
        logger.warning(f"Failed to setup default OTLP exporter: {e}")

def _setup_metrics(resource: Resource, enable_console_export: bool) -> None:
    """Setup metrics with readers and exporters"""
    global _meter_provider
    
    readers = []
    
    # Add console exporter for development
    if enable_console_export:
        console_reader = PeriodicExportingMetricReader(
            exporter=ConsoleMetricExporter(),
            export_interval_millis=30000,  # 30 seconds
        )
        readers.append(console_reader)
    
    # Create meter provider
    _meter_provider = MeterProvider(
        resource=resource,
        metric_readers=readers
    )
    metrics.set_meter_provider(_meter_provider)

def _setup_auto_instrumentation() -> None:
    """Setup automatic instrumentation for common libraries"""
    try:
        # FastAPI instrumentation
        FastAPIInstrumentor().instrument()
        logger.info("FastAPI instrumentation enabled")
        
        # HTTPX instrumentation
        HTTPXClientInstrumentor().instrument()
        logger.info("HTTPX instrumentation enabled")
        
        # SQLAlchemy instrumentation
        SQLAlchemyInstrumentor().instrument()
        logger.info("SQLAlchemy instrumentation enabled")
        
    except Exception as e:
        logger.warning(f"Failed to setup auto instrumentation: {e}")

def get_tracer(name: str):
    """
    Get a tracer instance
    
    Args:
        name: Name of the tracer (usually module name)
        
    Returns:
        Tracer instance
    """
    if not _is_initialized:
        setup_observability()
    
    return trace.get_tracer(name)

def get_meter(name: str):
    """
    Get a meter instance
    
    Args:
        name: Name of the meter (usually module name)
        
    Returns:
        Meter instance
    """
    if not _is_initialized:
        setup_observability()
    
    return metrics.get_meter(name)