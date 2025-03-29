import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:savvy_expense_tracker/providers/auth.dart';
import 'package:savvy_expense_tracker/screens/auth.dart';
import 'package:savvy_expense_tracker/screens/home.dart';

class AuthGate extends StatelessWidget {
  const AuthGate({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<AuthProvider>(
      builder: (context, auth, child) {
        print("Is not empty ${auth.accessToken?.isNotEmpty}");
        if (auth.accessToken?.isNotEmpty == true) {
          return const HomePage();
        }
        return const AuthPage();
      },
    );
  }
}
