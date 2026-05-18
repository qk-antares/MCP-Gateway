(function () {
  'use strict';

  const API = '/api';
  let state = { servers: [], selectedId: null, showModal: false, tools: [], toolsLoading: false };
  let pollTimer = null;

  // ── API ──

  async function request(url, options) {
    const res = await fetch(API + url, { headers: { 'Content-Type': 'application/json' }, ...options });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || '请求失败: ' + res.status);
    }
    return res.json();
  }

  async function fetchServers() {
    const data = await request('/servers');
    return data.servers;
  }

  async function createServer(data) {
    return request('/servers', { method: 'POST', body: JSON.stringify(data) });
  }

  async function deleteServer(id) {
    return request('/servers/' + id, { method: 'DELETE' });
  }

  async function toggleServer(id) {
    return request('/servers/' + id + '/toggle', { method: 'PATCH' });
  }

  async function fetchServerTools(id) {
    const data = await request('/servers/' + id + '/tools');
    return data.tools;
  }

  async function fetchOAuthUrl(id) {
    const data = await request('/servers/' + id + '/oauth-url');
    return data.oauth_url;
  }

  // ── Render ──

  function render() {
    const app = document.getElementById('app');
    app.innerHTML = renderServerPanel() + renderToolPanel();
    if (state.showModal) renderModal();
    setupPolling();
  }

  function renderServerPanel() {
    let cards = '';
    if (state.servers.length === 0) {
      cards = '<div class="empty-state"><p>暂无 MCP Server</p><p class="sub">点击上方"+ 添加"按钮开始</p></div>';
    } else {
      cards = '<div class="server-list">' + state.servers.map(renderServerCard).join('') + '</div>';
    }
    return `<div>
      <div class="panel-header">
        <h2>MCP Servers</h2>
        <button class="btn btn-primary" onclick="app.openModal()">+ 添加</button>
      </div>
      ${cards}
    </div>`;
  }

  function renderServerCard(s) {
    const selected = s.id === state.selectedId;
    const disabled = s.status === 'disabled';
    let cls = 'server-card';
    if (selected) cls += ' selected';
    if (disabled) cls += ' disabled';

    const statusCls = 'badge badge-' + s.status;
    const statusLabels = { active: '已连接', pending: '连接中', error: '错误', disabled: '已停用' };
    const statusLabel = statusLabels[s.status] || s.status;

    const toggleIcon = disabled
      ? '<svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M5.636 5.636a9 9 0 1012.728 0M12 3v9"/></svg>'
      : '<svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>';
    const toggleCls = disabled ? 'icon-btn toggle-on' : 'icon-btn toggle';
    const toggleTitle = disabled ? '启用' : '停用';

    const url = s.transport_type === 'http' ? (s.url || '') : (s.command || '');

    let extra = '';
    if (s.status === 'pending' && s.auth_type === 'oauth') {
      extra = `<button class="oauth-btn" onclick="event.stopPropagation(); app.handleOAuth(${s.id})">点击进行 OAuth 授权</button>`;
    }
    if (s.status === 'error' && s.error_message) {
      extra = `<div class="error-msg" title="${escHtml(s.error_message)}">${escHtml(s.error_message)}</div>`;
    }

    return `<div class="${cls}" onclick="app.selectServer(${s.id})">
      <div class="server-card-top">
        <div class="server-card-info">
          <h3>${escHtml(s.name)}</h3>
          <div class="server-card-meta">
            <span class="badge badge-transport">${s.transport_type}</span>
            <span class="${statusCls}">${statusLabel}</span>
          </div>
          <div class="server-card-url">${escHtml(url)}</div>
          <div class="server-card-tools">${s.tool_count} 个工具</div>
        </div>
        <div class="server-card-actions">
          <button class="${toggleCls}" title="${toggleTitle}" onclick="event.stopPropagation(); app.toggle(${s.id})">${toggleIcon}</button>
          <button class="icon-btn delete" title="删除" onclick="event.stopPropagation(); app.remove(${s.id})">
            <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
          </button>
        </div>
      </div>
      ${extra}
    </div>`;
  }

  function renderToolPanel() {
    const server = state.servers.find(s => s.id === state.selectedId);
    if (!server) {
      return '<div class="tool-panel-empty">选择一个 MCP Server 查看工具列表</div>';
    }
    if (state.toolsLoading) {
      return '<div class="tool-panel"><h2>' + escHtml(server.name) + ' 的工具</h2><p class="loading">加载中...</p></div>';
    }
    const url = server.transport_type === 'http' ? (server.url || '') : (server.command || '');
    let items = '';
    if (state.tools.length === 0) {
      items = '<p class="tool-panel-empty">暂无工具</p>';
    } else {
      items = '<div class="tool-list">' + state.tools.map(t =>
        `<div class="tool-item"><h4>${escHtml(t.name)}</h4>${t.description ? '<p>' + escHtml(t.description) + '</p>' : ''}</div>`
      ).join('') + '</div>';
    }
    return `<div class="tool-panel">
      <h2>${escHtml(server.name)} 的工具</h2>
      <p class="subtitle">${escHtml(url)}</p>
      ${items}
    </div>`;
  }

  function renderModal() {
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.onclick = (e) => { if (e.target === overlay) closeModal(); };
    overlay.innerHTML = `<div class="modal">
      <h2>添加 MCP Server</h2>
      <div class="form-group">
        <label>名称</label>
        <input id="f-name" placeholder="例如: GitHub MCP">
      </div>
      <div class="form-group">
        <label>协议类型</label>
        <div class="type-toggle">
          <button class="active" data-type="http" onclick="app.switchType(this)">HTTP</button>
          <button data-type="stdio" onclick="app.switchType(this)">STDIO</button>
        </div>
      </div>
      <div class="form-group" id="fg-url">
        <label>URL</label>
        <input id="f-url" placeholder="http://localhost:8080/mcp" style="font-family:monospace">
      </div>
      <div class="form-group" id="fg-cmd" style="display:none">
        <label>命令</label>
        <input id="f-cmd" placeholder="uvx mcp-server-xxx --arg1 val1" style="font-family:monospace">
        <div class="hint">输入完整命令，空格分隔参数</div>
      </div>
      <div class="form-group">
        <label>认证方式</label>
        <select id="f-auth" onchange="app.authChange()">
          <option value="none">无认证</option>
          <option value="api_key">API Key</option>
          <option value="bearer">Bearer Token</option>
          <option value="oauth">OAuth</option>
        </select>
      </div>
      <div class="form-group" id="fg-token" style="display:none">
        <label id="f-token-label">Token</label>
        <input id="f-token" type="password" style="font-family:monospace">
      </div>
      <div id="modal-error" class="form-group" style="display:none"><p class="error"></p></div>
      <div class="modal-actions">
        <button class="btn btn-secondary" onclick="app.closeModal()">取消</button>
        <button class="btn btn-primary" id="btn-submit" onclick="app.submitServer()">添加</button>
      </div>
    </div>`;
    document.body.appendChild(overlay);
  }

  // ── Actions ──

  function openModal() { state.showModal = true; render(); }
  function closeModal() { state.showModal = false; document.querySelector('.modal-overlay')?.remove(); }

  function switchType(btn) {
    btn.parentElement.querySelectorAll('button').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const isHttp = btn.dataset.type === 'http';
    document.getElementById('fg-url').style.display = isHttp ? '' : 'none';
    document.getElementById('fg-cmd').style.display = isHttp ? 'none' : '';
  }

  function authChange() {
    const auth = document.getElementById('f-auth').value;
    const show = auth === 'api_key' || auth === 'bearer';
    document.getElementById('fg-token').style.display = show ? '' : 'none';
    document.getElementById('f-token-label').textContent = auth === 'api_key' ? 'API Key' : 'Bearer Token';
  }

  async function submitServer() {
    const name = document.getElementById('f-name').value.trim();
    if (!name) return;
    const typeBtn = document.querySelector('.type-toggle button.active');
    const transport_type = typeBtn ? typeBtn.dataset.type : 'http';
    const auth_type = document.getElementById('f-auth').value;
    const tokenVal = document.getElementById('f-token').value.trim();

    const data = { name, transport_type, auth_type };
    if (transport_type === 'http') {
      data.url = document.getElementById('f-url').value.trim();
    } else {
      const parts = document.getElementById('f-cmd').value.trim().split(/\s+/);
      data.command = parts[0];
      if (parts.length > 1) data.args = parts.slice(1);
    }
    if ((auth_type === 'api_key' || auth_type === 'bearer') && tokenVal) {
      data.auth_config = auth_type === 'api_key' ? { api_key: tokenVal } : { token: tokenVal };
    }

    const errEl = document.getElementById('modal-error');
    const btn = document.getElementById('btn-submit');
    btn.disabled = true; btn.textContent = '添加中...';
    try {
      await createServer(data);
      closeModal();
      await reload();
    } catch (e) {
      errEl.style.display = '';
      errEl.querySelector('p').textContent = e.message;
    } finally {
      btn.disabled = false; btn.textContent = '添加';
    }
  }

  async function selectServer(id) {
    state.selectedId = id;
    state.toolsLoading = true;
    render();
    try {
      state.tools = await fetchServerTools(id);
    } catch { state.tools = []; }
    state.toolsLoading = false;
    render();
  }

  async function toggle(id) {
    await toggleServer(id);
    await reload();
  }

  async function remove(id) {
    if (!confirm('确认删除此 MCP Server？')) return;
    await deleteServer(id);
    if (state.selectedId === id) { state.selectedId = null; state.tools = []; }
    await reload();
  }

  async function handleOAuth(id) {
    const url = await fetchOAuthUrl(id);
    if (url) window.open(url, '_blank', 'width=600,height=700');
  }

  // ── Polling ──

  function setupPolling() {
    const hasPending = state.servers.some(s => s.status === 'pending');
    if (hasPending && !pollTimer) {
      pollTimer = setInterval(reload, 3000);
    } else if (!hasPending && pollTimer) {
      clearInterval(pollTimer);
      pollTimer = null;
    }
  }

  async function reload() {
    state.servers = await fetchServers();
    if (state.selectedId) {
      const still = state.servers.find(s => s.id === state.selectedId);
      if (!still) { state.selectedId = null; state.tools = []; }
    }
    render();
  }

  // ── Util ──

  function escHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  // ── Init ──

  async function init() {
    document.getElementById('app').innerHTML = '<p class="loading">加载中...</p>';
    state.servers = await fetchServers();
    render();
  }

  window.app = { openModal, closeModal, switchType, authChange, submitServer, selectServer, toggle, remove, handleOAuth };
  document.addEventListener('DOMContentLoaded', init);
})();
