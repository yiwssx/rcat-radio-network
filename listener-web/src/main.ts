import App from './App.svelte';
import './app.css';
import { mount } from 'svelte';

const target = document.getElementById('app');
if (!target) throw new Error('Missing #app mount element');
mount(App, { target });
