import 'package:flutter/material.dart';
import 'screens/signup.dart';

void main() {
  runApp(const MaterialApp(title: 'Savvy', home: Home()));
}

class Home extends StatelessWidget {
  const Home({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Savvy Expense Tracker App')),
      body: Column(
        children: [
          ElevatedButton(
            onPressed:
                () => {
                  Navigator.push(
                    context,
                    MaterialPageRoute(builder: (context) => const SignupPage()),
                  ),
                },
            child: const Text('Sign up'),
          ),
          ElevatedButton(onPressed: null, child: const Text('Log in')),
        ],
      ),
    );
  }
}
