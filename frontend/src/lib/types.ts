export interface Team {
    id: number;
    name: string;
    is_admin: boolean;
}

export interface Submission {
    id: number;
    team_id: number;
    task_id: number;
    public_score: number;
    private_score: number;
    timestamp: string;
    details: string;
}

export interface LeaderboardEntry {
    team_name: string;
    score: number;
    rank: number;
    private_score?: number;
}

export interface Answer {
    id: number;
    question_id: number;
    team_id: number;
    content: string;
    author_name: string;
    author_is_admin: boolean;
    created_at: string;
    updated_at: string;
}

export interface Question {
    id: number;
    team_id: number;
    title: string;
    content: string;
    author_name: string;
    author_is_admin: boolean;
    created_at: string;
    updated_at: string;
    answer_count: number;
    latest_answers: Answer[];
}

export interface QuestionDetail extends Question {
    all_answers: Answer[];
}
