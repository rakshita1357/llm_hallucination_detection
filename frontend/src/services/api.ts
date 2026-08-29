import type { AnalysisReport, Claim, Message } from '@/types';

/**
 * Sends a user message to the backend (or mock) and returns the AI answer plus analysis.
 * @param conversationId Unique identifier for the chat session.
 * @param modelId Identifier of the selected AI model.
 * @param message The user input.
 */
export async function sendMessage(
  conversationId: string,
  modelId: string,
  message: string,
): Promise<{ answer: string; claims: Claim[]; analysis: AnalysisReport }> {
  // Development mock – provides deterministic data without external services.
  if (import.meta.env.DEV) {
    return new Promise((resolve) => {
      setTimeout(() => {
        const mockClaims: Claim[] = [
          {
            id: 'claim-1',
            text: 'Mock claim about the response.',
            confidenceScore: 0.92,
            evidence: [
              {
                id: 'evidence-1',
                title: 'Mock source',
                snippet: 'This is a snippet from a mocked source supporting the claim.',
                url: 'https://example.com/mock-source',
              },
            ],
          },
          {
            id: 'claim-2',
            text: 'Another mock claim with lower confidence.',
            confidenceScore: 0.68,
            evidence: [],
          },
        ];

        const mockAnalysis: AnalysisReport = {
          riskLevel: 'LOW',
          riskScore: 15,
          totalClaims: mockClaims.length,
          supportedClaims: 1,
          uncertainClaims: 1,
          contradictedClaims: 0,
          claims: mockClaims,
        };

        resolve({
          answer: `This is a mock AI response for \"${message}\" using model ${modelId}.`,
          claims: mockClaims,
          analysis: mockAnalysis,
        });
      }, 800);
    });
  }

  // Production request – forwards to backend API.
  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: modelId,
      message,
      conversation_id: conversationId,
    }),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`API error ${response.status}: ${text}`);
  }

  // Expected shape matches the mock response.
  const data = await response.json();
  return data;
}
