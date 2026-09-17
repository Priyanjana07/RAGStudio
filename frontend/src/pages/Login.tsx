import { useState } from "react";
import api from "../services/api";
import "./Login.css";
interface LoginProps {
    onLogin: () => void;
}

function Login({ onLogin }: LoginProps) {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const handleLogin = async () => {
        if (!email.trim() || !password.trim()) {
            setError("Please enter your email and password.");
            return;
        }

        setLoading(true);
        setError("");

        try {
            const response = await api.post("/auth/login", {
                email: email,
                password: password,
            });

            const token = response.data.access_token;

            localStorage.setItem("access_token", token);

            onLogin();
        } catch (err: any) {
            setError(
                err.response?.data?.detail ||
                "Login failed."
            );
        } finally {
            setLoading(false);
        }
    };

    return (
        <main className="login-page">
            <div className="login-card">
                <p className="login-eyebrow">RAGVIZ</p>

                <h1>Welcome back</h1>

                <p className="login-subtitle">
                    Sign in to access your document workspace.
                </p>

                <div className="login-form">
                    <label>Email</label>

                    <input
                        type="email"
                        placeholder="Enter your email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                    />

                    <label>Password</label>

                    <input
                        type="password"
                        placeholder="Enter your password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        onKeyDown={(e) => {
                            if (e.key === "Enter") {
                                handleLogin();
                            }
                        }}
                    />

                    {error && (
                        <div className="login-error">
                            {error}
                        </div>
                    )}

                    <button
                        onClick={handleLogin}
                        disabled={loading}
                    >
                        {loading ? "Signing in..." : "Sign In"}
                    </button>
                </div>
            </div>
        </main>
    );
}

export default Login;