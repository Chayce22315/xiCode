import SwiftUI

struct ContentView: View {
    @State private var projects: [String] = ["MyFirstApp", "LiquidGlassDemo"]
    @State private var selectedProject: String? = "MyFirstApp"
    @State private var codeText: String = """
    #import <Foundation/Foundation.h>
    
    int main(int argc, const char * argv[]) {
        @autoreleasepool {
            NSLog(@"Hello, Pixelated Studios!");
        }
        return 0;
    }
    """

    var body: some View {
        NavigationView {
            // Sidebar: Project Navigator
            List(projects, id: \.self, selection: $selectedProject) { project in
                NavigationLink(destination: EditorView(projectName: project, code: $codeText)) {
                    Label(project, systemImage: "folder.badge.gearshape")
                }
            }
            .navigationTitle("xiCode Projects")
            
            // Default placeholder view when no project is actively selected
            Text("Select or create a workspace project to begin compiling.")
                .font(.subheadline)
                .foregroundColor(.secondary)
        }
    }
}

struct EditorView: View {
    let projectName: String
    @Binding var code: String

    var body: some View {
        VComponents
    }
    
    private var VComponents: some View {
        VStack(spacing: 0) {
            // TextEditor serving as a basic code plane
            TextEditor(text: $code)
                .font(.system(.body, design: .monospaced))
                .autocapitalization(.none)
                .disableAutocorrection(true)
                .padding(4)
            
            // Action console drawer
            HStack {
                Button(action: { print("Compile initiated...") }) {
                    Label("Compile", systemImage: "play.fill")
                        .foregroundColor(.green)
                        .padding()
                }
                Spacer()
            }
            .background(Color(UIColor.secondarySystemBackground))
        }
        .navigationTitle(projectName)
        .navigationBarTitleDisplayMode(.inline)
    }
}