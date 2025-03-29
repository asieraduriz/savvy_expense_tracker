import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:savvy_expense_tracker/gates/auth.dart';
import 'package:savvy_expense_tracker/providers/auth.dart';
import 'package:savvy_expense_tracker/services/auth.dart';

void main() {
  runApp(
    ChangeNotifierProvider(
      create: (context) => AuthProvider(authService: AuthService()),
      child: const MaterialApp(title: 'Savvy', home: AuthGate()),
    ),
  );
}
