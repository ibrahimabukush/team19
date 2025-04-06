import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { MessageCircle } from 'lucide-react';
import axios from 'axios';

const AcademicRequestsForm = () => {
  const [selectedRequestType, setSelectedRequestType] = useState("");
  const [requestText, setRequestText] = useState("");
  const [aiSuggestion, setAiSuggestion] = useState("");
  const [attachment, setAttachment] = useState(null);
  const [message, setMessage] = useState("");

  const academicTypes = [
    "Get enrollment or grade confirmations",
    "Submit academic appeals",
    "Request exam reviews"
  ];

  const generateAiSuggestion = () => {
    const suggestions = {
      "Submit academic appeals": "I am writing to appeal my grade in [Course Name] taught by Professor [Name] during the [Semester/Year]. I believe my grade of [Grade] does not accurately reflect my performance because [specific reason]. I completed all assignments, attended all classes, and my overall coursework demonstrates a higher level of achievement. I have attached [relevant documents] to support my appeal.",
      "Request exam reviews": "I would like to request a review of my exam for [Course Name] taken on [Date]. I believe there may have been an error in the grading of questions [specify question numbers if possible]. My answer to question [number] addressed all the key points including [briefly explain]."
    };

    setAiSuggestion(suggestions[selectedRequestType] || "Start by clearly stating your request and provide any relevant details or documentation.");
  };

  const useAiSuggestion = () => {
    setRequestText(aiSuggestion);
    setAiSuggestion("");
  };

  const handleSubmit = async () => {
    const formData = new FormData();
    formData.append("request_type", selectedRequestType);
    formData.append("request_text", requestText);
    if (attachment) formData.append("attachment", attachment);

    try {
      const response = await axios.post('/api/submit-request', formData);
      setMessage("Request submitted successfully!");
      setSelectedRequestType("");
      setRequestText("");
      setAttachment(null);
    } catch (error) {
      console.error(error);
      setMessage("An error occurred while submitting your request.");
    }
  };

  return (
    <div className="max-w-3xl mx-auto p-4">
      <Card className="w-full">
        <CardHeader>
          <CardTitle className="text-2xl font-bold text-center">Academic Requests</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            <div className="space-y-2">
              <label className="text-lg font-medium">Request Type:</label>
              <select
                className="w-full p-2 border rounded"
                value={selectedRequestType}
                onChange={(e) => {
                  setSelectedRequestType(e.target.value);
                  setRequestText("");
                  setAiSuggestion("");
                }}
              >
                <option value="">Select a request type</option>
                {academicTypes.map((type) => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
            </div>

            {selectedRequestType && (
              <>
                <div className="space-y-2 mt-4">
                  <label className="font-medium">Request Details:</label>
                  <Textarea 
                    className="w-full p-2 min-h-32 border rounded" 
                    placeholder="Describe your request in detail"
                    value={requestText}
                    onChange={(e) => setRequestText(e.target.value)}
                  />
                </div>

                <div className="space-y-2 mt-4">
                  <label className="font-medium">Attachments (if applicable):</label>
                  <input 
                    type="file" 
                    className="w-full p-2 border rounded" 
                    multiple
                    onChange={(e) => setAttachment(e.target.files[0])}
                  />
                </div>

                {(selectedRequestType === "Submit academic appeals" || selectedRequestType === "Request exam reviews") && (
                  <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
                    <div className="flex items-center gap-2 mb-3">
                      <MessageCircle className="text-blue-500" />
                      <h3 className="font-bold text-blue-700">AI Writing Assistant</h3>
                    </div>

                    {!aiSuggestion ? (
                      <div>
                        <p className="mb-2">Need help writing your request? Our AI assistant can provide a template.</p>
                        <Button 
                          onClick={generateAiSuggestion}
                          className="bg-blue-500 hover:bg-blue-600 text-white"
                        >
                          Generate Template
                        </Button>
                      </div>
                    ) : (
                      <div>
                        <p className="mb-2 font-medium">Suggested template:</p>
                        <div className="p-3 bg-white rounded border mb-3">
                          {aiSuggestion}
                        </div>
                        <Button 
                          onClick={useAiSuggestion}
                          className="bg-blue-500 hover:bg-blue-600 text-white"
                        >
                          Use This Template
                        </Button>
                      </div>
                    )}
                  </div>
                )}
              </>
            )}

            {selectedRequestType && (
              <div className="pt-4">
                <Button onClick={handleSubmit} className="w-full bg-green-600 hover:bg-green-700 text-white py-2 px-4 rounded">
                  Submit Request
                </Button>
              </div>
            )}

            {message && (
              <div className="text-center mt-4 font-medium text-blue-600">{message}</div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default AcademicRequestsForm;
