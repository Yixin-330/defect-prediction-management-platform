/**
 * Agent Bridge — connects the frontend UI to the Multi-Agent backend.
 *
 * API client for the Supervisor + Sub-Agent architecture.
 * Provides both simple fetch and SSE streaming support.
 */

const AGENT_BRIDGE = {
  BASE_URL: 'http://localhost:8000/api',

  /**
   * Full Supervisor workflow — sends user query, all agents run.
   */
  async query(query, stream = false) {
    const res = await fetch(`${this.BASE_URL}/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, stream }),
    });
    if (!res.ok) {
      const err = await res.text();
      throw new Error(`Agent query failed: ${err}`);
    }
    return res.json();
  },

  /**
   * SSE streaming workflow — agents report progress as they run.
   * onProgress(phase, status, data) called for each event.
   * onComplete(answer) called when all agents finish.
   */
  queryStream(query, { onPhase, onProgress, onComplete, onError } = {}) {
    const url = `${this.BASE_URL}/query/stream`;
    const es = new EventSourcePolyfill(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, stream: true }),
    });

    // Since fetch-based SSE is custom, we use fetch + ReadableStream
    this._streamFetch(url, query, { onPhase, onProgress, onComplete, onError });
  },

  async _streamFetch(url, query, { onPhase, onProgress, onComplete, onError }) {
    try {
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, stream: true }),
      });

      if (!res.ok) {
        onError?.(await res.text());
        return;
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed || trimmed.startsWith(':')) continue;
          if (trimmed === 'data: [DONE]') {
            onComplete?.();
            return;
          }

          const jsonStr = trimmed.replace(/^data: /, '');
          try {
            const event = JSON.parse(jsonStr);
            this._handleEvent(event, { onPhase, onProgress, onComplete, onError });
          } catch (e) {
            console.warn('[AgentBridge] Parse error:', e, 'line:', trimmed);
          }
        }
      }
    } catch (err) {
      onError?.(err.message);
    }
  },

  _handleEvent(event, { onPhase, onProgress, onComplete, onError }) {
    switch (event.type) {
      case 'status':
        onProgress?.(event.message);
        break;
      case 'intent':
        onPhase?.('intent', 'done', event.intent);
        break;
      case 'phase':
        onPhase?.(event.phase, event.status, event.summary || event);
        break;
      case 'complete':
        onComplete?.(event.answer, event.elapsed);
        break;
      case 'error':
        onError?.(event.error);
        break;
    }
  },

  /**
   * Individual Agent endpoints (for targeted requests)
   */
  async runAgent(agentName, task, country = 'id', category = '', budget = 'mid') {
    const res = await fetch(`${this.BASE_URL}/${agentName}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ task, country, category, budget }),
    });
    if (!res.ok) throw new Error(`${agentName} agent failed`);
    return res.json();
  },

  async trend(country = 'id', category = '') {
    return this.runAgent('trend', `分析${country}市场趋势`, country, category);
  },

  async competitor(country = 'id', category = '') {
    return this.runAgent('competitor', `分析${country}竞品`, country, category);
  },

  async recommend(country = 'id', budget = 'mid', category = '') {
    return this.runAgent('recommend', `为${country}推荐选品`, country, category, budget);
  },

  async profit(country = 'id', category = '') {
    return this.runAgent('profit', `计算${country}利润`, country, category);
  },

  async report(task = '生成综合报告', country = 'id') {
    return this.runAgent('report', task, country);
  },

  async health() {
    const res = await fetch(`${this.BASE_URL}/health`);
    return res.json();
  },
};

/**
 * Fallback: if EventSource isn't available, use polyfill behavior.
 * We use fetch-based SSE above, so this is just a placeholder for the interface.
 */
class EventSourcePolyfill {
  constructor(url, options) {
    this.url = url;
    this.options = options;
  }
  close() {}
}
