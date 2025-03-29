import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:savvy_expense_tracker/providers/auth.dart';

class AuthPage extends StatefulWidget {
  const AuthPage({super.key});

  @override
  State<AuthPage> createState() => _AuthPageState();
}

class _AuthPageState extends State<AuthPage> {
  bool _showLoginUI = true;

  // Controllers for Login form
  final TextEditingController _loginEmailController = TextEditingController();
  final TextEditingController _loginPasswordController =
      TextEditingController();

  // Controllers for Signup form
  final TextEditingController _signupEmailController = TextEditingController();
  final TextEditingController _signupUsernameController =
      TextEditingController();
  final TextEditingController _signupPasswordController =
      TextEditingController();

  @override
  void dispose() {
    _loginEmailController.dispose();
    _loginPasswordController.dispose();
    _signupEmailController.dispose();
    _signupUsernameController.dispose();
    _signupPasswordController.dispose();
    super.dispose();
  }

  void _toggleAuthMode() {
    setState(() {
      _showLoginUI = !_showLoginUI;
    });
  }

  Future<void> _handleLogin(BuildContext context) async {
    final authProvider = Provider.of<AuthProvider>(context, listen: false);
    await authProvider.login(
      _loginEmailController.text.trim(),
      _loginPasswordController.text.trim(),
    );
  }

  Future<void> _handleSignup(BuildContext context) async {
    final authProvider = Provider.of<AuthProvider>(context, listen: false);
    await authProvider.signup(
      _signupUsernameController.text.trim(),
      _signupEmailController.text.trim(),
      _signupPasswordController.text.trim(),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(_showLoginUI ? 'Login' : 'Sign Up')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            if (_showLoginUI)
              _buildLoginForm(context)
            else
              _buildSignupForm(context),
            const SizedBox(height: 24.0),
            TextButton(
              onPressed: _toggleAuthMode,
              child: Text(
                _showLoginUI
                    ? "Don't have an account? Sign up"
                    : 'Already have an account? Log in',
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLoginForm(BuildContext context) {
    final authProvider = Provider.of<AuthProvider>(context); // To access state

    return Column(
      children: [
        TextField(
          controller: _loginEmailController,
          keyboardType: TextInputType.emailAddress,
          decoration: const InputDecoration(labelText: 'Email'),
        ),
        const SizedBox(height: 16.0),
        TextField(
          controller: _loginPasswordController,
          obscureText: true,
          decoration: const InputDecoration(labelText: 'Password'),
        ),
        const SizedBox(height: 24.0),
        ElevatedButton(
          onPressed:
              authProvider.status == AuthStatus.authenticating
                  ? null
                  : () => _handleLogin(context),
          child:
              authProvider.status == AuthStatus.authenticating
                  ? const CircularProgressIndicator()
                  : const Text('Login'),
        ),
        if (authProvider.errorMessage != null && _showLoginUI)
          Padding(
            padding: const EdgeInsets.only(top: 8.0),
            child: Text(
              authProvider.errorMessage!,
              style: TextStyle(color: Theme.of(context).colorScheme.error),
              textAlign: TextAlign.center,
            ),
          ),
      ],
    );
  }

  Widget _buildSignupForm(BuildContext context) {
    final authProvider = Provider.of<AuthProvider>(context); // To access state

    return Column(
      children: [
        TextField(
          controller: _signupEmailController,
          keyboardType: TextInputType.emailAddress,
          decoration: const InputDecoration(labelText: 'Email'),
        ),
        const SizedBox(height: 16.0),
        TextField(
          controller: _signupUsernameController,
          decoration: const InputDecoration(labelText: 'Username'),
        ),
        const SizedBox(height: 16.0),
        TextField(
          controller: _signupPasswordController,
          obscureText: true,
          decoration: const InputDecoration(labelText: 'Password'),
        ),
        const SizedBox(height: 24.0),
        ElevatedButton(
          onPressed:
              authProvider.status == AuthStatus.authenticating
                  ? null
                  : () => _handleSignup(context),
          child:
              authProvider.status == AuthStatus.authenticating
                  ? const CircularProgressIndicator()
                  : const Text('Sign Up'),
        ),
        if (authProvider.errorMessage != null && !_showLoginUI)
          Padding(
            padding: const EdgeInsets.only(top: 8.0),
            child: Text(
              authProvider.errorMessage!,
              style: TextStyle(color: Theme.of(context).colorScheme.error),
              textAlign: TextAlign.center,
            ),
          ),
      ],
    );
  }
}
