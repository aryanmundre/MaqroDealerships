import { supabase } from "./supabase";

export async function changePassword(
    oldPw: string,
    newPw: string
) {
    const { data: { user }, error: signInErr } = await supabase.auth.signInWithPassword({
        email: (await supabase.auth.getUser()).data.user?.email ?? "",
        password: oldPw,
    })
    if (signInErr || !user) throw new Error("Current password is incorrect")
    
    const { error: updateErr} = await supabase.auth.updateUser({
        password: newPw,
    })
    if (updateErr) throw new Error(updateErr.message || "Failed to update password")

}