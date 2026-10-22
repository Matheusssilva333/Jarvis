export interface Project {
  id: string;
  title: string;
  description: string;
  tags: string[];
  imageUrl: string;
  link?: string;
}

export interface Skill {
  name: string;
  category: string;
  proficiency: number;
  details?: string[];
}

export interface Experience {
  id: string;
  company: string;
  position: string;
  period: string;
  description: string;
  achievements: string[];
}

export interface Education {
  id: string;
  institution: string;
  degree: string;
  period: string;
  description?: string;
}

export interface Idioma {
  name: string;
  category: string;
  proficiency: number;
}

export interface Feedback {
  id: string;
  description: string;
  imageUrls: string[];
}

export interface Client {
  id: string;
  name: string;
  role: string;
  tags: string[];
  avatarUrl?: string;
}

export interface Message {
  role: 'user' | 'assistant';
  content: string;
}