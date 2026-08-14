import { useEffect, useRef, useState, useCallback } from "react";
import { getOrchestratorApiBaseUrl } from "../config/config";

export function useOrchestratorEvents(workflowId, onEventReceived) {
  const [isConnected, setIsConnected] = useState(false);
  const [events, setEvents] = useState([]);
  const [error, setError] = useState(null);
  const lastSeqRef = useRef(0);
  const eventSourceRef = useRef(null);

  const connect = useCallback(() => {
    if (!workflowId) return;

    const baseUrl = getOrchestratorApiBaseUrl();
    const sseUrl = `${baseUrl}/${workflowId}/events?after_sequence=${lastSeqRef.current}`;

    try {
      const es = new EventSource(sseUrl);
      eventSourceRef.current = es;

      es.onopen = () => {
        setIsConnected(true);
        setError(null);
      };

      es.onmessage = (e) => {
        try {
          const parsed = JSON.parse(e.data);
          if (parsed.sequence_number && parsed.sequence_number > lastSeqRef.current) {
            lastSeqRef.current = parsed.sequence_number;
            setEvents((prev) => [...prev, parsed]);
            if (onEventReceived) {
              onEventReceived(parsed);
            }
          }
        } catch (err) {
          console.debug("SSE Parse notice:", err);
        }
      };

      // Listen for named event types
      const eventTypes = [
        "workflow_created",
        "plan_created",
        "plan_updated",
        "node_started",
        "node_completed",
        "node_failed",
        "artifact_written",
        "interrupt_requested",
        "hitl_resolved",
        "workflow_cancelled",
        "workflow_completed",
        "workflow_failed",
      ];

      eventTypes.forEach((type) => {
        es.addEventListener(type, (e) => {
          try {
            const parsed = JSON.parse(e.data);
            if (parsed.sequence_number && parsed.sequence_number > lastSeqRef.current) {
              lastSeqRef.current = parsed.sequence_number;
              setEvents((prev) => [...prev, parsed]);
              if (onEventReceived) {
                onEventReceived(parsed);
              }
            }
          } catch (err) {
            console.debug(`SSE event ${type} notice:`, err);
          }
        });
      });

      es.onerror = (err) => {
        setIsConnected(false);
        // EventSource automatically retries connection
      };
    } catch (err) {
      setError(err.message);
      setIsConnected(false);
    }
  }, [workflowId, onEventReceived]);

  useEffect(() => {
    connect();
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, [connect]);

  return { isConnected, events, error, lastSequence: lastSeqRef.current };
}
