import React, { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from './api';

interface User {
    id: number;
    name: string;
    is_admin: boolean;
}

interface AuthContextType {
    user: User | null;
    token: string | null;
    login: (name: string, password: string) => Promise<void>;
    logout: () => void;
    isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const loadUser = async () => {
            if (token) {
                try {
                    const response = await authAPI.getCurrentUser();
                    setUser(response.data);
                } catch (error) {
                    console.error('Failed to load user:', error);
                    localStorage.removeItem('token');
                    setToken(null);
                }
            }
            setIsLoading(false);
        };

        loadUser();
    }, [token]);

    const login = async (name: string, password: string) => {
        const response = await authAPI.login(name, password);
        const { access_token } = response.data;
        localStorage.setItem('token', access_token);
        setToken(access_token);

        // Fetch user info
        const userResponse = await authAPI.getCurrentUser();
        setUser(userResponse.data);
    };

    const logout = () => {
        localStorage.removeItem('token');
        setToken(null);
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{ user, token, login, logout, isLoading }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};
