import React, { useState, useEffect } from 'react';
import { qaAPI } from '@/lib/api';
import type { Question, QuestionDetail } from '@/lib/types';
import { useAuth } from '@/lib/auth';

const QASection: React.FC = () => {
    const { user } = useAuth();
    const [questions, setQuestions] = useState<Question[]>([]);
    const [selectedQuestion, setSelectedQuestion] = useState<QuestionDetail | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [view, setView] = useState<'list' | 'detail' | 'create'>('list');

    // Form states
    const [newQuestionTitle, setNewQuestionTitle] = useState('');
    const [newQuestionContent, setNewQuestionContent] = useState('');
    const [newAnswerContent, setNewAnswerContent] = useState('');

    useEffect(() => {
        if (view === 'list') {
            fetchQuestions();
        }
    }, [view]);

    const fetchQuestions = async () => {
        setIsLoading(true);
        try {
            const response = await qaAPI.getQuestions();
            setQuestions(response.data);
        } catch (error) {
            console.error('Failed to fetch questions:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleQuestionClick = async (id: number) => {
        setIsLoading(true);
        try {
            const response = await qaAPI.getQuestion(id);
            setSelectedQuestion(response.data);
            setView('detail');
        } catch (error) {
            console.error('Failed to fetch question details:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleCreateQuestion = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        try {
            await qaAPI.createQuestion(newQuestionTitle, newQuestionContent);
            setNewQuestionTitle('');
            setNewQuestionContent('');
            setView('list');
        } catch (error: any) {
            alert(error.response?.data?.detail || 'Failed to create question');
        } finally {
            setIsLoading(false);
        }
    };

    const handleCreateAnswer = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!selectedQuestion) return;

        setIsLoading(true);
        try {
            await qaAPI.createAnswer(selectedQuestion.id, newAnswerContent);
            setNewAnswerContent('');
            // Refresh details
            handleQuestionClick(selectedQuestion.id);
        } catch (error: any) {
            alert(error.response?.data?.detail || 'Failed to post answer');
        } finally {
            setIsLoading(false);
        }
    };

    const handleDeleteQuestion = async (id: number) => {
        if (!confirm('Delete this question?')) return;
        try {
            await qaAPI.deleteQuestion(id);
            if (view === 'detail') setView('list');
            else fetchQuestions();
        } catch (error) {
            console.error('Failed to delete question:', error);
        }
    };

    const handleDeleteAnswer = async (id: number) => {
        if (!confirm('Delete this answer?')) return;
        try {
            await qaAPI.deleteAnswer(id);
            if (selectedQuestion) handleQuestionClick(selectedQuestion.id);
        } catch (error) {
            console.error('Failed to delete answer:', error);
        }
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleString();
    };

    if (view === 'create') {
        return (
            <div className="max-w-4xl mx-auto">
                <button
                    onClick={() => setView('list')}
                    className="mb-4 text-sm hover:underline"
                    style={{ color: 'var(--primary)' }}
                >
                    ← Back to Questions
                </button>
                <div className="rounded-lg border p-6" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)' }}>
                    <h2 className="text-xl font-bold mb-6" style={{ color: 'var(--foreground)' }}>Ask a Question</h2>
                    <form onSubmit={handleCreateQuestion} className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium mb-1" style={{ color: 'var(--foreground)' }}>Title</label>
                            <input
                                type="text"
                                value={newQuestionTitle}
                                onChange={(e) => setNewQuestionTitle(e.target.value)}
                                className="w-full px-4 py-2 rounded-md border focus:outline-none focus:ring-2"
                                style={{ backgroundColor: 'var(--background)', borderColor: 'var(--border)', color: 'var(--foreground)' }}
                                required
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium mb-1" style={{ color: 'var(--foreground)' }}>Content</label>
                            <textarea
                                value={newQuestionContent}
                                onChange={(e) => setNewQuestionContent(e.target.value)}
                                rows={6}
                                className="w-full px-4 py-2 rounded-md border focus:outline-none focus:ring-2"
                                style={{ backgroundColor: 'var(--background)', borderColor: 'var(--border)', color: 'var(--foreground)' }}
                                required
                            />
                        </div>
                        <button
                            type="submit"
                            disabled={isLoading}
                            className="px-6 py-2 rounded-md font-semibold transition-all hover:opacity-90"
                            style={{ backgroundColor: 'var(--primary)', color: 'var(--background)' }}
                        >
                            {isLoading ? 'Posting...' : 'Post Question'}
                        </button>
                    </form>
                </div>
            </div>
        );
    }

    if (view === 'detail' && selectedQuestion) {
        return (
            <div className="max-w-4xl mx-auto">
                <button
                    onClick={() => setView('list')}
                    className="mb-4 text-sm hover:underline"
                    style={{ color: 'var(--primary)' }}
                >
                    ← Back to Questions
                </button>

                {/* Question Detail */}
                <div className="rounded-lg border p-6 mb-6" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)' }}>
                    <div className="flex justify-between items-start mb-4">
                        <h2 className="text-2xl font-bold" style={{ color: 'var(--foreground)' }}>{selectedQuestion.title}</h2>
                        {user?.is_admin && (
                            <button
                                onClick={() => handleDeleteQuestion(selectedQuestion.id)}
                                className="text-red-500 hover:text-red-400 text-sm"
                            >
                                Delete
                            </button>
                        )}
                    </div>
                    <div className="text-sm mb-4 flex gap-4" style={{ color: 'var(--muted-foreground)' }}>
                        <span>Posted by <span className={selectedQuestion.author_is_admin ? "text-purple-400 font-bold" : ""}>{selectedQuestion.author_name}</span></span>
                        <span>{formatDate(selectedQuestion.created_at)}</span>
                    </div>
                    <div className="whitespace-pre-wrap mb-6 text-lg" style={{ color: 'var(--foreground)' }}>
                        {selectedQuestion.content}
                    </div>
                </div>

                {/* Answers List */}
                <div className="space-y-4 mb-8">
                    <h3 className="text-xl font-bold mb-4" style={{ color: 'var(--foreground)' }}>
                        Answers ({selectedQuestion.all_answers.length})
                    </h3>
                    {selectedQuestion.all_answers.map((answer) => (
                        <div
                            key={answer.id}
                            className={`rounded-lg border p-4 ${answer.author_is_admin ? 'border-l-4' : ''}`}
                            style={{
                                backgroundColor: 'var(--card)',
                                borderColor: answer.author_is_admin ? 'var(--accent)' : 'var(--border)'
                            }}
                        >
                            <div className="flex justify-between items-start mb-2">
                                <div className="text-sm" style={{ color: 'var(--muted-foreground)' }}>
                                    <span className={`font-medium ${answer.author_is_admin ? 'text-purple-400 text-base' : ''}`}>
                                        {answer.author_name} {answer.author_is_admin && '(Admin)'}
                                    </span>
                                    <span className="mx-2">•</span>
                                    {formatDate(answer.created_at)}
                                </div>
                                {user?.is_admin && (
                                    <button
                                        onClick={() => handleDeleteAnswer(answer.id)}
                                        className="text-red-500 hover:text-red-400 text-xs"
                                    >
                                        Delete
                                    </button>
                                )}
                            </div>
                            <div className="whitespace-pre-wrap" style={{ color: 'var(--foreground)' }}>
                                {answer.content}
                            </div>
                        </div>
                    ))}
                    {selectedQuestion.all_answers.length === 0 && (
                        <p className="text-center py-8 italic" style={{ color: 'var(--muted-foreground)' }}>
                            No answers yet.
                        </p>
                    )}
                </div>

                {/* Post Answer Form */}
                <div className="rounded-lg border p-6" style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)' }}>
                    <h3 className="text-lg font-bold mb-4" style={{ color: 'var(--foreground)' }}>Post an Answer</h3>
                    <form onSubmit={handleCreateAnswer} className="space-y-4">
                        <textarea
                            value={newAnswerContent}
                            onChange={(e) => setNewAnswerContent(e.target.value)}
                            rows={4}
                            className="w-full px-4 py-2 rounded-md border focus:outline-none focus:ring-2"
                            style={{ backgroundColor: 'var(--background)', borderColor: 'var(--border)', color: 'var(--foreground)' }}
                            placeholder="Write your answer here..."
                            required
                        />
                        <button
                            type="submit"
                            disabled={isLoading}
                            className="px-6 py-2 rounded-md font-semibold transition-all hover:opacity-90"
                            style={{ backgroundColor: 'var(--primary)', color: 'var(--background)' }}
                        >
                            {isLoading ? 'Posting...' : 'Post Answer'}
                        </button>
                    </form>
                </div>
            </div>
        );
    }

    return (
        <div className="max-w-4xl mx-auto space-y-6">
            <div className="flex justify-between items-center">
                <h2 className="text-2xl font-bold" style={{ color: 'var(--foreground)' }}>Community Q&A</h2>
                <button
                    onClick={() => setView('create')}
                    className="px-4 py-2 rounded-md font-semibold transition-all hover:opacity-90"
                    style={{ backgroundColor: 'var(--primary)', color: 'var(--background)' }}
                >
                    Ask a Question
                </button>
            </div>

            <div className="space-y-4">
                {questions.map((q) => (
                    <div
                        key={q.id}
                        onClick={() => handleQuestionClick(q.id)}
                        className="rounded-lg border p-6 cursor-pointer hover:border-blue-500 transition-all"
                        style={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)' }}
                    >
                        <div className="flex justify-between items-start mb-2">
                            <h3 className="text-lg font-bold hover:text-blue-400" style={{ color: 'var(--foreground)' }}>
                                {q.title}
                            </h3>
                            <div className="flex items-center gap-3">
                                <span className="text-xs bg-gray-800 px-2 py-1 rounded" style={{ color: 'var(--muted-foreground)' }}>
                                    {q.answer_count} answers
                                </span>
                                {user?.is_admin && (
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            handleDeleteQuestion(q.id);
                                        }}
                                        className="text-red-500 hover:text-red-400 text-xs px-2 py-1 rounded hover:bg-red-900/20"
                                    >
                                        Delete
                                    </button>
                                )}
                            </div>
                        </div>

                        <div className="text-sm mb-4 flex gap-2" style={{ color: 'var(--muted-foreground)' }}>
                            <span className={q.author_is_admin ? "text-purple-400" : ""}>{q.author_name}</span>
                            <span>•</span>
                            <span>{formatDate(q.created_at)}</span>
                        </div>

                        <p className="line-clamp-2 mb-4" style={{ color: 'var(--muted-foreground)' }}>
                            {q.content}
                        </p>

                        {/* Preview latest comments */}
                        {q.latest_answers.length > 0 && (
                            <div className="mt-4 pt-4 border-t space-y-3" style={{ borderColor: 'rgba(255,255,255,0.1)' }}>
                                {q.latest_answers.map(a => (
                                    <div key={a.id} className="text-sm flex gap-2">
                                        <div className={`font-semibold shrink-0 ${a.author_is_admin ? 'text-purple-400' : 'text-gray-400'}`}>
                                            {a.author_name}:
                                        </div>
                                        <div className="truncate" style={{ color: 'var(--muted-foreground)' }}>
                                            {a.content}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                ))}

                {questions.length === 0 && !isLoading && (
                    <div className="text-center py-12 rounded-lg border border-dashed" style={{ borderColor: 'var(--border)' }}>
                        <p style={{ color: 'var(--muted-foreground)' }}>No questions yet. Be the first to ask!</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default QASection;
