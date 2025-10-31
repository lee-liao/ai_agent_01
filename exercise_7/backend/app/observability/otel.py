"""
OpenTelemetry observability setup with Tracer, Metrics, and Exporter initialization
Includes span attributes for tool.name, retries, latency_ms, and status
"""

import os
import logging
from typing import Optional, Dict, Any
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

def setup_observability() -> None:
    """
    Initialize OpenTelemetry observability stack with configuration from environment variables
    """
    global _tracer_provider, _meter_provider, _is_initialized
    
    if _is_initialized:
        logger.info("Observability already initialized")
        return
    
    # Get configuration from environment variables
    config = get_observability_config()
    
    # Debug logging to see what configuration is being used
    logger.info(f"Observability config: {config}")
    logger.info(f"JAEGER_ENDPOINT environment variable: {os.getenv('JAEGER_ENDPOINT')}")
    
    logger.info("Initializing OpenTelemetry observability...")
    
    # Create resource with service information
    resource = Resource.create({
        "service.name": config["service_name"],
        "service.version": config["service_version"],
        "service.instance.id": os.getenv("HOSTNAME", "localhost"),
    })
    
    # Setup tracing
    _setup_tracing(resource, config["jaeger_endpoint"], config["enable_console_export"])
    
    # Setup metrics
    _setup_metrics(resource, config["enable_console_export"])
    
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
    else:
        # Add default OTLP exporter for local development only when no jaeger endpoint is provided
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

def shutdown_observability():
    """Shutdown observability providers"""
    global _tracer_provider, _meter_provider, _is_initialized
    
    if _tracer_provider:
        _tracer_provider.shutdown()
    
    if _meter_provider:
        _meter_provider.shutdown()
    
    _is_initialized = False
    logger.info("Observability shutdown complete")

# Environment-based configuration
def get_observability_config() -> Dict[str, Any]:
    """Get observability configuration from application settings"""
    from app.config import settings
    
    return {
        "service_name": settings.otel_service_name,
        "service_version": settings.otel_service_version,
        "jaeger_endpoint": settings.jaeger_endpoint,
        "enable_console_export": settings.otel_console_export,
    }
