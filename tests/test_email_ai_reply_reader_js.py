"""Exercise reader AI Reply, insertion results and context retention in Node."""

from pathlib import Path

import pytest

from test_email_ai_reply_ui_js import _between, _run


ROOT = Path(__file__).resolve().parents[1]


def _reader(scenario):
    source = (ROOT / "static/js/emailInbox.js").read_text()
    functions = "\n".join((
        _between(source, "function _cleanAiReplyText(", "let _emails ="),
        _between(source, "async function _openEmail(", "function _showEmailMenu("),
    )).replace("import('./ui.js')", "Promise.resolve(uiModule)")
    fixtures = r"""
      const API_BASE = '', _replySeparator = '---------- Previous message ----------';
      let _openEmailRequestSeq = 0, _currentFolder = 'INBOX';
      const window = {__odysseusActiveEmailAccount: 'account-a', _myEmailAddresses: ['morgan@example.invalid']};
      const uiMessages = [], openedDocs = [], requests = [];
      const uiModule = {showError(text) { uiMessages.push(text); }, showToast() {}};
      const sessionModule = {getCurrentModel() { return ''; }, getCurrentSessionId() { return 'session-a'; }};
      const em = {uid: '42', subject: 'Visit', account_id: 'account-a'};
      const data = {
        ...em, from_name: 'Taylor', from_address: 'taylor@example.invalid',
        to: 'morgan@example.invalid', message_id: '<visit@example.invalid>',
        body: 'Could you confirm a suitable day for the visit?', date: '2026-10-01T12:00:00Z',
      };
      let existingDocId = null, replacementResult = true;
      const replacements = [];
      const _docModule = {
        findEmailDocId() { return existingDocId; }, isPanelOpen() { return true; },
        openPanel() {}, async loadDocument() {}, async ensureEmailDraftEnvelope() {},
        injectFreshDoc(doc) { openedDocs.push(doc); },
        async replaceEmailReplyBody(id, text, opts) {
          replacements.push({id, text, opts}); return replacementResult;
        },
      };
      async function _createEmailChat() { return 'reply-session'; }
      function _bringEmailReplyDraftToFrontOnMobile() {}
      function _isMyEmailAddress() { return false; }
      function _withoutMyAddresses() { return []; }
      function buildReplyAllCc() { return ''; }
      function requestAnimationFrame(callback) { callback(); }
      function setTimeout() { return 1; }
      function clearTimeout() {}
      const console = {error() {}, warn() {}};
      const document = {};
      let fetch = async (url, opts) => {
        const payload = opts?.body ? JSON.parse(opts.body) : null;
        requests.push({url, payload});
        if (url.endsWith('/ai-reply')) return response();
        if (url.endsWith('/document')) return {ok: true, status: 200, json: async () => ({id: 'fresh-draft', ...payload})};
        throw new Error('Unexpected endpoint');
      };
      async function flush() { for (let i = 0; i < 8; i++) await Promise.resolve(); }
    """
    _run(scenario, functions, fixtures)


def test_reader_inserts_only_finished_reply_and_keeps_hint_and_source_scope():
    _reader(r"""
      const defaultFetch = fetch;
      fetch = async (url, opts) => {
        if (url.endsWith('/ai-reply')) {
          requests.push({url, payload: JSON.parse(opts.body)});
          return response('<think>Need to confirm Thursday.</think>\n<<<REPLY>>>' + finalReply + '<<<END>>>\nDone');
        }
        return defaultFetch(url, opts);
      };
      assert.equal(await _openEmail(em, null, data, 'ai-reply-fast', hint), true);
      assert.equal(requests[0].payload.user_hint, hint);
      assert.equal(requests[0].payload.original_body, data.body);
      assert.equal(requests[0].payload.account_id, 'account-a');
      assert.equal(requests[0].payload.uid, '42');
      assert.equal(requests[0].payload.folder, 'INBOX');
      assert.equal(openedDocs.length, 1);
      assert.ok(openedDocs[0].content.includes('\n---\n' + finalReply + '\n\n' + _replySeparator));
      assert.doesNotMatch(openedDocs[0].content, /Need to confirm|<<<|\nDone/);
    """)


@pytest.mark.parametrize("reply", ["Done", "<think>Need to reply.</think>", "<<<REPLY>>>partial"])
def test_reader_unusable_reply_does_not_create_or_overwrite_a_draft(reply):
    import json
    _reader(r"""
      fetch = async () => response(""" + json.dumps(reply) + r""");
      assert.equal(!!(await _openEmail(em, null, data, 'ai-reply-fast', hint)), false);
      await flush();
      assert.equal(openedDocs.length, 0);
      assert.equal(replacements.length, 0);
      assert.equal(uiMessages.length, 1);
      assert.match(uiMessages[0], /no usable reply/);
    """)


def test_reader_stale_account_response_does_not_open_a_draft():
    _reader(r"""
      const pending = deferred(); fetch = async () => pending.promise;
      const generation = _openEmail(em, null, data, 'ai-reply-fast', hint);
      window.__odysseusActiveEmailAccount = 'account-b';
      pending.resolve(response());
      assert.equal(!!(await generation), false);
      assert.equal(openedDocs.length, 0);
      assert.equal(uiMessages.length, 0);
    """)


def test_reader_invalid_legacy_cached_reply_requests_a_fresh_answer():
    _reader(r"""
      window.__odysseusActiveEmailAccount = '';
      delete data.account_id; delete em.account_id;
      data.cached_ai_reply = 'Done';
      assert.equal(await _openEmail(em, null, data, 'ai-reply'), true);
      assert.equal(requests.filter(r => r.url.endsWith('/ai-reply')).length, 1);
      assert.ok(openedDocs[0].content.includes(finalReply));
    """)


@pytest.mark.parametrize("inserted", [True, False])
def test_reader_success_signal_matches_actual_existing_draft_insertion(inserted):
    import json
    _reader(r"""
      existingDocId = 'existing-draft'; replacementResult = """ + json.dumps(inserted) + r""";
      assert.equal(await _openEmail(em, null, data, 'ai-reply-fast', hint), replacementResult);
      assert.equal(openedDocs.length, 0);
      assert.equal(replacements.length, 1);
      assert.equal(replacements[0].text, finalReply);
      assert.equal(replacements[0].opts.userHint, hint);
      assert.equal(replacements[0].opts.force, false);
    """)


def _context(scenario):
    source = (ROOT / "static/js/emailLibrary.js").read_text()
    functions = _between(source, "async function _runAiReplyFromButton(", "function _handleAiReplyButton(")
    fixtures = r"""
      const btn = {
        disabled: false, innerHTML: 'AI reply', dataset: {},
        closest() { return {}; }, appendChild() {},
        getBoundingClientRect() { return {left: 12, top: 100, bottom: 130}; },
      };
      const em = {uid: '42'}, data = {_aiReplyNoteHint: hint};
      let callbackResult = false;
      const state = {_onEmailClick: async () => callbackResult};
      const spinnerModule = {createWhirlpool() { return {element: {style: {}}, stop() {}}; }};
      function _snapEmailModalToLeftSidebar() {}
      function topPortalZ() { return 100; }
      function setTimeout() { return 1; }
      const window = {innerWidth: 1440, innerHeight: 1000};
      const inputHandlers = {}, menuHandlers = {};
      const noteInput = {value: '', focus() {}, addEventListener(name, callback) { inputHandlers[name] = callback; }};
      const menu = {
        style: {}, className: '', innerHTML: '', remove() {}, contains() { return false; },
        querySelector() { return noteInput; },
        addEventListener(name, callback) { menuHandlers[name] = callback; },
      };
      const document = {
        querySelectorAll() { return []; }, createElement() { return menu; },
        removeEventListener() {}, addEventListener() {}, body: {appendChild() {}},
      };
    """
    _run(scenario, functions, fixtures)


def test_reader_context_note_survives_failed_attempt_and_is_prefilled():
    _context(r"""
      assert.equal(await _runAiReplyFromButton(btn, em, data, 'ai-reply-fast', hint), false);
      assert.equal(data._aiReplyNoteHint, hint);
      assert.equal(btn.disabled, false);
      assert.equal(btn.innerHTML, 'AI reply');
      _showAiReplyChoice(btn, em, data);
      assert.equal(noteInput.value, hint);
      noteInput.value = 'Please confirm Thursday in one sentence'; inputHandlers.input();
      assert.equal(data._aiReplyNoteHint, noteInput.value);
    """)


def test_reader_context_note_clears_only_after_successful_insertion():
    _context(r"""
      callbackResult = true;
      assert.equal(await _runAiReplyFromButton(btn, em, data, 'ai-reply-fast', hint), true);
      assert.equal(Object.hasOwn(data, '_aiReplyNoteHint'), false);
      assert.equal(btn.disabled, false);
    """)
