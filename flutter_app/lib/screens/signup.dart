import 'package:flutter/material.dart';
import 'login.dart';

class SignupPage extends StatelessWidget {
  const SignupPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(),
      body: Padding(
        padding: EdgeInsets.all(16.0),
        child: Form(
          child: Column(
            children: [
              TextFormField(decoration: InputDecoration(labelText: 'Name')),
              TextFormField(decoration: InputDecoration(labelText: 'Email')),
              TextFormField(decoration: InputDecoration(labelText: 'Password')),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: [
                  FilledButton(onPressed: () {}, child: const Text('Sign up')),
                  TextButton(
                    onPressed: () {
                      Navigator.pushReplacement(
                        context,
                        MaterialPageRoute(
                          builder: (context) => const LoginPage(),
                        ),
                      );
                    },
                    child: const Text("Or log in"),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
